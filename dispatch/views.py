from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import CSVFileUploadForm
from .models import CSVFileUpload


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

            return HttpResponseRedirect(reverse('index'))

        else:
            # todo: return error message
            print('form not valid')
            pass

    return render(request, 'dispatch/upload_csv.html', {'form': form})