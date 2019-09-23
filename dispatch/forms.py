from django import forms
from .models import CSVFileUpload


class CSVFileUploadForm(forms.ModelForm):
    class Meta:
        model = CSVFileUpload
        fields = ['file']