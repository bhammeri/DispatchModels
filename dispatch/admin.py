from django.contrib import admin

from .models import CSVFileUpload


# Register your models here.
class CSVFileUploadAdmin(admin.ModelAdmin):
    list_filter = ['upload_date']


admin.site.register(CSVFileUpload, CSVFileUploadAdmin)