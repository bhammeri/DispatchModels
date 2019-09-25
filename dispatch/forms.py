from django import forms
from .models import CSVFileUpload, ThermalPlant


class CSVFileUploadForm(forms.ModelForm):
    class Meta:
        model = CSVFileUpload
        fields = ['file']


class ThermalPlantForm(forms.ModelForm):
    class Meta:
        model = ThermalPlant
        fields = ['name', 'capacity', 'efficiency', 'MIN_prod_fraction', 'SEL_prod_fraction', 'MEL_prod_fraction',
                  'ramping_rate_BSE', 'ramping_rate_RMP', 'ramping_rate_NRM', 'ramping_costs_BSE', 'ramping_costs_RMP',
                  'ramping_costs_NRM', 'depreciation', 'shutdown_costs', 'hot_start_costs', 'warm_start_costs',
                  'cold_start_costs', 'hot_start_within_timedelta', 'warm_start_within_timedelta']
