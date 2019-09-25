from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import CSVFileUploadForm, ThermalPlantForm
from .models import CSVFileUpload, ThermalPlant, create_thermal_plant_dispatch_model
from .utils import to_dict


# Create your views here.
@login_required
def upload_csv_file(request):
    form = CSVFileUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            # add user
            csv_file_upload = form.save(commit=False)
            csv_file_upload.user = request.user
            csv_file_upload.save()

            return HttpResponseRedirect(reverse('dispatch:dispatch-csv-upload'))

        else:
            # todo: return error message
            print('form not valid')
            pass

    return render(request, 'dispatch/upload_csv.html', {'form': form})


def _get_form(request, formcls, prefix):
    data = request.POST if prefix in request.POST else None
    return formcls(data, prefix=prefix)


@login_required
def create_thermal_plant_upload_csv(request):
    initial_plant_parameters = {'capacity': 100,
                                'efficiency': 0.5,
                                'MIN_prod_fraction': 0.2,
                                'SEL_prod_fraction': 0.8,
                                'MEL_prod_fraction': 1.0,
                                'ramping_rate_BSE': 0,
                                'ramping_rate_RMP': 0.025,
                                'ramping_rate_NRM': 0.1,
                                'ramping_costs_BSE': 30,
                                'ramping_costs_RMP': 25,
                                'ramping_costs_NRM': 20,
                                'depreciation': 2,
                                'shutdown_costs': 0,
                                'hot_start_costs': 20,
                                'warm_start_costs': 21,
                                'cold_start_costs': 22,
                                'hot_start_within_timedelta': 3,
                                'warm_start_within_timedelta': 12}

    plant_form = ThermalPlantForm(initial=initial_plant_parameters, prefix='plant')
    csv_form = CSVFileUploadForm(initial=None, files=None, prefix='csv')

    if request.method == 'POST':
        print(request.POST.keys())
        plant_form = ThermalPlantForm(request.POST, prefix='plant')

        if plant_form.is_valid():
            plant = plant_form.save(commit=False)
            print(plant.name, plant.capacity)
        else:
            print('not valid')

        csv_form = CSVFileUploadForm(request.POST, request.FILES, prefix='csv')
        if csv_form.is_valid():
            print('csv is valid')
            csv = csv_form.save(commit=False)
            csv.user = request.user
            csv.save()
            print(csv.to_dataframe())

        # todo: create plant and csv, read csv.to_dataframe, and call
        plant_definition = to_dict(plant)
        print(plant_definition)

        # todo: make it possible to hand over csv class instead of data directly
        df = csv.to_dataframe()

        # todo: serialize numpy array (int, float, datetime)
        time_series_index_data = df['index'].values.tolist()
        wholesale_price = df['wholesale_price'].values.tolist()
        clean_fuel_price = df['clean_fuel_price'].values.tolist()

        print(time_series_index_data, wholesale_price, clean_fuel_price)

        create_thermal_plant_dispatch_model(request.user, 0, plant_definition, time_series_index_data, wholesale_price, clean_fuel_price, pk=None)

    return render(request, 'dispatch/plant_csv.html', {'plant_form': plant_form, 'csv_form': csv_form})


@login_required
def create_themal_plant(request):
    initial_plant_parameters = {'capacity': 100,
                                'efficiency': 0.5,
                                'MIN_prod_fraction': 0.2,
                                'SEL_prod_fraction': 0.8,
                                'MEL_prod_fraction': 1.0,
                                'ramping_rate_BSE': 0,
                                'ramping_rate_RMP': 0.025,
                                'ramping_rate_NRM': 0.1,
                                'ramping_costs_BSE': 30,
                                'ramping_costs_RMP': 25,
                                'ramping_costs_NRM': 20,
                                'depreciation': 2,
                                'shutdown_costs': 0,
                                'hot_start_costs': 20,
                                'warm_start_costs': 21,
                                'cold_start_costs': 22,
                                'hot_start_within_timedelta': 3,
                                'warm_start_within_timedelta': 12}

    form = ThermalPlantForm(request.POST or initial_plant_parameters)

    if request.method == 'POST':
        if form.is_valid():
            thermal_plant = form.save(commit=False)
            thermal_plant.user = request.user
            thermal_plant.save()

            return HttpResponseRedirect(reverse('dispatch:create-thermal-plant'))

    return render(request, 'dispatch/thermal_plant_create.html', {'form': form})
