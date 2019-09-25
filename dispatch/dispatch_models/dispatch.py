from __future__ import division
from pyomo.environ import *
from pyomo.opt import SolverFactory 
import pandas as pd
import sqlite3
import os
import sys
import time

print("Argument1",sys.argv[1])
print("Argument2", sys.argv[2])

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#import and slice price series
df = pd.read_excel('main.xlsx', sheet_name=0) # can also index sheet by name or fetch all sheets

slice_start = 0 # must be less than slice_end
slice_end   = 200 # max 8760 as main.xlsx contains only one year


time_stamp=list(range(slice_end-slice_start))

power_price = df['power prices'].tolist()
power_price = power_price[slice_start:slice_end]
power_price = dict(zip(time_stamp, power_price))

clean_fuel_price = df['clean fuel price'].tolist()
clean_fuel_price = clean_fuel_price[slice_start:slice_end]
clean_fuel_price = dict(zip(time_stamp, clean_fuel_price))

#time_stamp = ['h{}'.format("%04d" % i) for i in range(len(power_price))]


class Plant:
    def __init__(self,
                 MW_installed,
                 efficiency,
                 rampingRates,
                 rampingCosts,
                 MIN_fraction,
                 SEL_fraction,
                 MEL_fraction,
                 
                 depriciation,
                 shutdown_cost,
                 hot_start_cost,
                 warm_start_cost,
                 cold_start_cost,
                 hotStartWithinTime,
                 warmStartWithinTime,
                 ):
        
        self.MW_installed = MW_installed
        
        self.n_efficiency = efficiency
        
        self.n_production = self.MW_installed
        self.n_consumption = self.MW_installed/self.n_efficiency
        
        
        rampingRates.update((x, y*self.MW_installed) for x, y in rampingRates.items())
        self.rampingRates = rampingRates
        
        self.rampingCosts = rampingCosts
        
        self.depriciation = depriciation*self.MW_installed
        
        
        self.MIN = MIN_fraction*self.MW_installed
        self.SEL = SEL_fraction*self.MW_installed
        self.MEL = MEL_fraction*self.MW_installed
        
        self.UPhot_cost = hot_start_cost*self.MW_installed
        self.UPwarm_cost = warm_start_cost*self.MW_installed
        self.UPcold_cost = cold_start_cost*self.MW_installed
        
        self.UPhot_time  = hotStartWithinTime
        self.UPwarm_time = warmStartWithinTime
        self.DW_cost = shutdown_cost*self.MW_installed
        
    
def optimize(plant, time_stamp, power_price, fuel_price):

    model = ConcreteModel()
    
    model.T = Set(initialize=time_stamp)

    model.power_price = Param(model.T, initialize = power_price)
    model.fuel_price  = Param(model.T, initialize = fuel_price)

    model.production = Var(model.T, within=NonNegativeReals)
    model.consumption = Var(model.T, within=NonNegativeReals)
    
    model.powerProdBSE = Var(model.T, within=NonNegativeReals)
    model.powerProdRMP = Var(model.T, within=NonNegativeReals)
    model.powerProdNRM = Var(model.T, within=NonNegativeReals)
           
    model.ONF = Var(model.T, within=Binary)
    model.RMP = Var(model.T, within=Binary)
    model.NRM = Var(model.T, within=Binary)
    
    model.status_def0 = ConstraintList(rule=(model.ONF[t]
                                             >=
                                             model.RMP[t]
                                             for t in model.T))
    
    model.status_def1 = ConstraintList(rule=(model.RMP[t]
                                             >=
                                             model.NRM[t]
                                             for t in model.T))
    
    model.powerProdBSE_def = ConstraintList(rule=(model.powerProdBSE[t]
                                                  ==
                                                  (plant.MIN-0)*model.ONF[t]
                                                  for t in model.T))
    
    model.powerProdRMP_def0 = ConstraintList(rule=((plant.SEL-plant.MIN)*model.NRM[t]
                                                   <=
                                                   model.powerProdRMP[t]
                                                   for t in model.T))
    model.powerProdRMP_def1 = ConstraintList(rule=(model.powerProdRMP[t]
                                                   <=
                                                   (plant.SEL-plant.MIN)*model.RMP[t]
                                                   for t in model.T))
    
    model.powerProdNRM_def0 = ConstraintList(rule=((plant.MEL-plant.SEL)*0
                                                   <=
                                                   model.powerProdNRM[t]
                                                   for t in model.T))
    model.powerProdNRM_def1 = ConstraintList(rule=(model.powerProdNRM[t]
                                                   <=
                                                   (plant.MEL-plant.SEL)*model.NRM[t]
                                                   for t in model.T))
        
    def RMP_constaintUP(model,t):
        if t == 0:
            return Constraint.Skip
        else:
            return (model.powerProdRMP[t]-model.powerProdRMP[t-1]
                    <=
                    + plant.rampingRates['RMP'])       
    model.RMP_UP = Constraint(model.T, rule=RMP_constaintUP) 
    
    def RMP_constaintDW(model,t):
        if t == 0:
            return Constraint.Skip
        else:
            return (model.powerProdRMP[t]-model.powerProdRMP[t-1]
                    >=
                    - plant.rampingRates['RMP']) 
    model.RMP_DW = Constraint(model.T, rule=RMP_constaintDW)  
        
    def NRM_constaintUP(model,t):
        if t == 0:
            return Constraint.Skip
        else:
            return (model.powerProdNRM[t]-model.powerProdNRM[t-1]
                    <=
                    + plant.rampingRates['NRM'])       
    model.NRM_UP = Constraint(model.T, rule=NRM_constaintUP) 
    
    def NRM_constaintDW(model,t):
        if t == 0:
            return Constraint.Skip
        else:
            return (model.powerProdNRM[t]-model.powerProdNRM[t-1]
                    >=
                    - plant.rampingRates['NRM']) 
    model.NRM_DW = Constraint(model.T, rule=NRM_constaintDW)     
    
    
    model.powerProdBSE_UP = Var(model.T, within=NonNegativeReals)
    model.powerProdBSE_DW = Var(model.T, within=NonNegativeReals)    
    model.powerProdRMP_UP = Var(model.T, within=NonNegativeReals)
    model.powerProdRMP_DW = Var(model.T, within=NonNegativeReals)
    model.powerProdNRM_UP = Var(model.T, within=NonNegativeReals)
    model.powerProdNRM_DW = Var(model.T, within=NonNegativeReals)
    
    def ramping(model,plant):
        
        def powerProdBSE_UPDW_contraint(model,i):
            if i ==0:
                return model.powerProdBSE_UP[i]+model.powerProdBSE_DW[i] == 0
            else:
                return model.powerProdBSE_UP[i]-model.powerProdBSE_DW[i] == model.powerProdBSE[i]-model.powerProdBSE[i-1]
        model.BSE_UPDW = Constraint(model.T, rule=powerProdBSE_UPDW_contraint)         
        
        def powerProdRMP_UPDW_contraint(model,i):
            if i ==0:
                return model.powerProdRMP_UP[i]+model.powerProdRMP_DW[i] == 0
            else:
                return model.powerProdRMP_UP[i]-model.powerProdRMP_DW[i] == model.powerProdRMP[i]-model.powerProdRMP[i-1]
        model.RMP_UPDW = Constraint(model.T, rule=powerProdRMP_UPDW_contraint)  

        def powerProdNRM_UPDW_contraint(model,i):
            if i ==0:
                return model.powerProdNRM_UP[i]+model.powerProdNRM_DW[i] == 0
            else:
                return model.powerProdNRM_UP[i]-model.powerProdNRM_DW[i] == model.powerProdNRM[i]-model.powerProdNRM[i-1]
        model.NRM_UPDW = Constraint(model.T, rule=powerProdNRM_UPDW_contraint) 
    
    ramping(model,plant)
    
    model.fuelCosts = Var(model.T, within=NonNegativeReals)    
    def fuelCosts(model,i):
        return (model.fuelCosts[i]
                ==
                model.consumption[i]*model.fuel_price[i])
    model.fuelCosts_def = Constraint(model.T, rule=fuelCosts)    
    
    model.rampingCosts = Var(model.T, within=NonNegativeReals)
    def rampingCosts(model,i):
        return (model.rampingCosts[i]
                ==
               + (model.powerProdBSE_UP[i] + model.powerProdBSE_DW[i])*plant.rampingCosts['BSE']
               + (model.powerProdRMP_UP[i] + model.powerProdRMP_DW[i])*plant.rampingCosts['RMP']
               + (model.powerProdNRM_UP[i] + model.powerProdNRM_DW[i])*plant.rampingCosts['NRM'])
    model.rampingCosts_def = Constraint(model.T, rule=rampingCosts)
    
    model.depriciationCosts = Var(model.T, within=NonNegativeReals)
    
    def depriciationCosts(model,i):
        return (model.depriciationCosts[i]
                ==
                + (model.ONF[i] - model.NRM[i])*plant.depriciation)
    model.depriciationCosts_def = Constraint(model.T, rule=depriciationCosts)
    
    model.production_def = ConstraintList(rule=(model.production[t]
                                                ==
                                                + model.powerProdBSE[t]
                                                + model.powerProdRMP[t]
                                                + model.powerProdNRM[t]
                                                for t in model.T))   
    
    model.consumption_def = ConstraintList(rule=(model.production[t]
                                                 ==
                                                 model.consumption[t]*plant.n_efficiency
                                                 for t in model.T))
    
    model.Revenues = Var(model.T) 
    model.Revenues_def = ConstraintList(rule= (model.Revenues[t]
                                               ==
                                               model.production[t]*model.power_price[t]
                                               for t in model.T))

    model.Costs = Var(model.T) 
    model.Costs_def = ConstraintList(rule= (model.Costs[t]
                                            == 
                                            + model.fuelCosts[t]
                                            + model.rampingCosts[t]
                                            + model.depriciationCosts[t]
                                            for t in model.T))   
    
    model.profit = Objective(expr= sum(model.Revenues[t] - model.Costs[t] for t in model.T), sense=maximize)

    # maybe to find cbc executable
    # try: os.environ[PATH] add path to executable + from pyutilib.services import register_executable, registered_executable // register_executable( name='glpsol')
    opt = SolverFactory('cbc') #options: 'couenne' for MINLP, 'glpk' or 'cbc' for MILP 
    result = opt.solve(model, tee=True)
    
    return {"model": model, "result": result}
    

myPlant = plant(MW_installed        = 100.00,
                efficiency          =   0.50,
                
                rampingRates        =  {'BSE':  0.000,
                                        'RMP':  0.025,
                                        'NRM':  0.100}, #fraction of total capacity
                rampingCosts        =  {'BSE': 30.000,
                                        'RMP': 25.000,
                                        'NRM': 20.000}, #EUR/MW
                
                depriciation        =  2.00, #EUR/MW if production < SEL
                
                MIN_fraction        =  0.20,
                SEL_fraction        =  0.80,
                MEL_fraction        =  1.00,
                hot_start_cost      = 20.00, #EUR/MW installed
                warm_start_cost     = 21.00, #EUR/MW installed
                cold_start_cost     = 22.00, #EUR/MW installed
                shutdown_cost       =  0.00, #EUR/MW installed
                hotStartWithinTime  =  3   , #Start counts as hot start if happening within x hours
                warmStartWithinTime = 12   , #Start counts as hot start if happening within x hours
               )

optimization = optimize(plant=myPlant,
                        time_stamp=time_stamp,
                        power_price=power_price,
                        fuel_price=clean_fuel_price)

result = optimization['result']
model = optimization['model']

#model.pprint()
result.write()

def addModelToDataframe(model, dataframe):
    seriesOutputList = []

    #Add paremeters to output dataframe
    for v in model.component_objects(Var, active=True):
        vDict = {key: value.value for key, value in v.items()}
        s = pd.Series(vDict, name = v.name)
        seriesOutputList.append(s)

    #Add variables to output dataframe
    for v in model.component_objects(Param, active=True):
        vDict = {key: value for key, value in v.items()}
        s = pd.Series(vDict, name = v.name)
        seriesOutputList.append(s)
        
    dataframe = pd.concat([pd.concat(seriesOutputList, axis=1), dataframe],axis = 0)
    
    return dataframe

dfOutput = pd.DataFrame()
dfOutput = addModelToDataframe(model=model, dataframe=dfOutput)
#dfOutput.to_excel("test.xlsx")
#input()

conn = sqlite3.connect('database.db')
dfOutput.to_sql('dispatch',conn,if_exists='replace')

sys.stdout.flush()