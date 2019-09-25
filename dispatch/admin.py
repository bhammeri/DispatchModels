from django.contrib import admin

from .models import CSVFileUpload, ThermalPlant, TimeSeriesIndex, TimeSeries, ThermalPlantDispatch


# Register your models here.
class CSVFileUploadAdmin(admin.ModelAdmin):
    list_filter = ['upload_date']


class ThermalPlantAdmin(admin.ModelAdmin):
    pass


class TimeSeriesIndexAdmin(admin.ModelAdmin):
    pass


class TimeSeriesAdmin(admin.ModelAdmin):
    pass


class ThermalPlantDispatchAdmin(admin.ModelAdmin):
    pass


admin.site.register(CSVFileUpload, CSVFileUploadAdmin)
admin.site.register(ThermalPlant, ThermalPlantAdmin)
admin.site.register(TimeSeriesIndex, TimeSeriesIndexAdmin)
admin.site.register(TimeSeries, TimeSeriesAdmin)
admin.site.register(ThermalPlantDispatch, ThermalPlantDispatchAdmin)