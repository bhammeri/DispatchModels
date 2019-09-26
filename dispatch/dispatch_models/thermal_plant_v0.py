from pyomo.environ import *
from pyomo.opt import SolverFactory 
import pandas as pd
from dispatch.dispatch_models.utils import register_cbc_executable, append_result_to_df, convert_model_result_to_dataframe


class ThermalPlantDispatchOptimizationModel(object):
    def __init__(self, plant_definition, time_series):
        """

        :param plant_definition: Dictionary of plant definition data defined in models.py ThermalPlant.
        :param time_series: Dataframe of input variables with the appropriate index (as index).
        """

        self._plant_definition = plant_definition
        self._input_data = time_series
        self._model = None
        self._optimization = None
        self._result = None

    def to_dataframe(self):
        return convert_model_result_to_dataframe(self._model)

    def optimize(self, start=None, end=None, number_of_batches=None, overlap=0.25):
        """
        Only allows for integer ranges (at the moment).
        :param overlap: (NOT IMPLEMENTED) If interval is optimized in batches, the overlap parameter defines how much
        overlap between batches is simulated to ease the boundary conditions for each batch.
        :param number_of_batches: The number of batches the given interal is split into.
        :param start: Offset for the given interval.
        :param end: End of the given interval
        :return:
        """
        # todo: increment must be changed to "number_of_batches" and then the setup of boundary condition must be met

        if start:
            assert start > 0, 'Start must be > 0.'
        else:
            start = 0

        if end:
            assert end < len(self._input_data), 'End must be smaller than length of data provided.'
        else:
            end = len(self._input_data)

        # setup variables for iteration
        increment = end-start

        if number_of_batches:
            increment = int(increment / number_of_batches)

        assert increment > 12, 'Each batch needs to be at least 12 data points.'

        # set overlap to nearest smaller integer
        overlap = int(overlap * increment)

        # todo: setup model and solve
        self._result = pd.DataFrame()
        for i in range(start, end, increment):
            slice_begin = i*start
            slice_end = (i+1)*end

            if slice_end > end:
                slice_end = end

            data_slice = self._input_data.iloc[slice_begin:slice_end]

            # create input data series for the optimization function
            # optimization functions needs a list of time indices
            # and dictionaries for the time series where the keys are the time indices and value the price values
            index = data_slice.index.tolist()
            wholesale_price = data_slice['wholesale_price'].to_dict()
            clean_fuel_price = data_slice['clean_fuel_price'].to_dict()

            # setup the optimization and optimize
            self._setup_optimization(self._plant_definition, index, wholesale_price, clean_fuel_price)
            self._optimize()
            iteration_result = self.to_dataframe()

            # add result to dataframe
            self._result = append_result_to_df(self._result, iteration_result)

        return self._result

    def _optimize(self):
        """

        :return:
        """

        register_cbc_executable()
        opt = SolverFactory('cbc')  # options: 'couenne' for MINLP, 'glpk' or 'cbc' for MILP
        self._optimization = opt.solve(self._model, tee=True)

        return {"model": self._model, "result": self._optimization}

    def _setup_optimization(self, plant, time_series_index, wholesale_price, clean_fuel_price, boundary_condition=None):
        """

        :param plant: Dictionary of plant definition
        :param time_series_index: List of index values (integer or time stamps)
        :param wholesale_price: dictionary key=time_series_index, value=price value in [EUR/MWh]
        :param clean_fuel_price: dictionary key=time_series_index, value=price value in [EUR/MWh]
        :return:
        """

        # todo: how to implement boundary condition

        self._model = ConcreteModel()

        self._model.T = Set(initialize=time_series_index)

        self._model.power_price = Param(self._model.T, initialize=wholesale_price)
        self._model.fuel_price = Param(self._model.T, initialize=clean_fuel_price)

        self._model.production = Var(self._model.T, within=NonNegativeReals)
        self._model.consumption = Var(self._model.T, within=NonNegativeReals)

        self._model.powerProdBSE = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdRMP = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdNRM = Var(self._model.T, within=NonNegativeReals)

        self._model.ONF = Var(self._model.T, within=Binary)
        self._model.RMP = Var(self._model.T, within=Binary)
        self._model.NRM = Var(self._model.T, within=Binary)

        self._model.status_def0 = ConstraintList(rule=(self._model.ONF[t]
                                                       >=
                                                       self._model.RMP[t]
                                                       for t in self._model.T))

        self._model.status_def1 = ConstraintList(rule=(self._model.RMP[t]
                                                       >=
                                                       self._model.NRM[t]
                                                       for t in self._model.T))

        self._model.powerProdBSE_def = ConstraintList(rule=(self._model.powerProdBSE[t]
                                                            ==
                                                            (plant['MIN'] - 0) * self._model.ONF[t]
                                                            for t in self._model.T))

        self._model.powerProdRMP_def0 = ConstraintList(rule=((plant['SEL'] - plant['MIN']) * self._model.NRM[t]
                                                             <=
                                                             self._model.powerProdRMP[t]
                                                             for t in self._model.T))

        self._model.powerProdRMP_def1 = ConstraintList(rule=(self._model.powerProdRMP[t]
                                                             <=
                                                             (plant['SEL'] - plant['MIN']) * self._model.RMP[t]
                                                             for t in self._model.T))

        self._model.powerProdNRM_def0 = ConstraintList(rule=((plant['MEL'] - plant['SEL']) * 0
                                                             <=
                                                             self._model.powerProdNRM[t]
                                                             for t in self._model.T))

        self._model.powerProdNRM_def1 = ConstraintList(rule=(self._model.powerProdNRM[t]
                                                             <=
                                                             (plant['MEL'] - plant['SEL']) * self._model.NRM[t]
                                                             for t in self._model.T))

        def RMP_constraint_up(model, t):
            if t == 0:
                return Constraint.Skip
            else:
                return (model.powerProdRMP[t] - model.powerProdRMP[t - 1]
                        <=
                        + plant['ramping_rate_RMP'])

        self._model.RMP_UP = Constraint(self._model.T, rule=RMP_constraint_up)

        def RMP_constraint_down(model, t):
            if t == 0:
                return Constraint.Skip
            else:
                return (model.powerProdRMP[t] - model.powerProdRMP[t - 1]
                        >=
                        - plant['ramping_rate_RMP'])

        self._model.RMP_DW = Constraint(self._model.T, rule=RMP_constraint_down)

        def NRM_constraint_up(model, t):
            if t == 0:
                return Constraint.Skip
            else:
                return (model.powerProdNRM[t] - model.powerProdNRM[t - 1]
                        <=
                        + plant['ramping_rate_NRM'])

        self._model.NRM_UP = Constraint(self._model.T, rule=NRM_constraint_up)

        def NRM_constraint_down(model, t):
            if t == 0:
                return Constraint.Skip
            else:
                return (model.powerProdNRM[t] - model.powerProdNRM[t - 1]
                        >=
                        - plant['ramping_rate_NRM'])

        self._model.NRM_DW = Constraint(self._model.T, rule=NRM_constraint_down)

        self._model.powerProdBSE_UP = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdBSE_DW = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdRMP_UP = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdRMP_DW = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdNRM_UP = Var(self._model.T, within=NonNegativeReals)
        self._model.powerProdNRM_DW = Var(self._model.T, within=NonNegativeReals)

        def ramping(model):

            def powerProdBSE_UPDW_contraint(model, i):
                if i == 0:
                    return model.powerProdBSE_UP[i] + model.powerProdBSE_DW[i] == 0
                else:
                    return model.powerProdBSE_UP[i] - model.powerProdBSE_DW[i] == model.powerProdBSE[i] - \
                           model.powerProdBSE[i - 1]

            model.BSE_UPDW = Constraint(self._model.T, rule=powerProdBSE_UPDW_contraint)

            def powerProdRMP_UPDW_contraint(model, i):
                if i == 0:
                    return model.powerProdRMP_UP[i] + model.powerProdRMP_DW[i] == 0
                else:
                    return model.powerProdRMP_UP[i] - model.powerProdRMP_DW[i] == model.powerProdRMP[i] - \
                           model.powerProdRMP[i - 1]

            model.RMP_UPDW = Constraint(self._model.T, rule=powerProdRMP_UPDW_contraint)

            def powerProdNRM_UPDW_contraint(model, i):
                if i == 0:
                    return model.powerProdNRM_UP[i] + model.powerProdNRM_DW[i] == 0
                else:
                    return model.powerProdNRM_UP[i] - model.powerProdNRM_DW[i] == model.powerProdNRM[i] - \
                           model.powerProdNRM[i - 1]

            model.NRM_UPDW = Constraint(self._model.T, rule=powerProdNRM_UPDW_contraint)

        ramping(self._model)

        self._model.fuelCosts = Var(self._model.T, within=NonNegativeReals)

        def fuelCosts(model, i):
            return (model.fuelCosts[i]
                    ==
                    model.consumption[i] * model.fuel_price[i])

        self._model.fuelCosts_def = Constraint(self._model.T, rule=fuelCosts)

        self._model.rampingCosts = Var(self._model.T, within=NonNegativeReals)

        def rampingCosts(model, i):
            return (model.rampingCosts[i]
                    ==
                    + (model.powerProdBSE_UP[i] + model.powerProdBSE_DW[i]) * plant['ramping_costs_BSE']
                    + (model.powerProdRMP_UP[i] + model.powerProdRMP_DW[i]) * plant['ramping_costs_RMP']
                    + (model.powerProdNRM_UP[i] + model.powerProdNRM_DW[i]) * plant['ramping_costs_NRM'])

        self._model.rampingCosts_def = Constraint(self._model.T, rule=rampingCosts)

        self._model.depriciationCosts = Var(self._model.T, within=NonNegativeReals)

        def depriciationCosts(model, i):
            return (model.depriciationCosts[i]
                    ==
                    + (model.ONF[i] - model.NRM[i]) * plant['depreciation']) # todo: ask if in MW or fraction

        self._model.depriciationCosts_def = Constraint(self._model.T, rule=depriciationCosts)

        self._model.production_def = ConstraintList(rule=(self._model.production[t]
                                                          ==
                                                          + self._model.powerProdBSE[t]
                                                          + self._model.powerProdRMP[t]
                                                          + self._model.powerProdNRM[t]
                                                          for t in self._model.T))

        self._model.consumption_def = ConstraintList(rule=(self._model.production[t]
                                                           ==
                                                           self._model.consumption[t] * plant['efficiency']
                                                           for t in self._model.T))

        self._model.Revenues = Var(self._model.T)
        self._model.Revenues_def = ConstraintList(rule=(self._model.Revenues[t]
                                                        ==
                                                        self._model.production[t] * self._model.power_price[t]
                                                        for t in self._model.T))

        self._model.Costs = Var(self._model.T)
        self._model.Costs_def = ConstraintList(rule=(self._model.Costs[t]
                                                     ==
                                                     + self._model.fuelCosts[t]
                                                     + self._model.rampingCosts[t]
                                                     + self._model.depriciationCosts[t]
                                                     for t in self._model.T))

        # objective function: maximize revenues
        self._model.profit = Objective(expr=sum(self._model.Revenues[t] - self._model.Costs[t] for t in self._model.T), sense=maximize)

        return self._model

