from django.urls import path, include
from . import views

app_name = 'dispatch'
urlpatterns = [
    path('csv/', include([
        path('upload/', views.upload_csv_file, name='csv-upload')
    ]))
]