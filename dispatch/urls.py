from django.urls import path, include
from . import views

app_name = 'dispatch'
urlpatterns = [
    path('csv/', include([
        path('upload/', views.upload_csv_file, name='dispatch-csv-upload')
    ])),
    path('thermal_plant/', include([
        path('create/', views.create_themal_plant, name='create-thermal-plant')
    ])),
    path('create_plant_csv/', views.create_thermal_plant_upload_csv, name='create-plant-upload-csv')
]