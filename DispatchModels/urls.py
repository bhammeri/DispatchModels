"""DispatchModels URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views import generic
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', generic.TemplateView.as_view(template_name='index.html'), name='index'),
    path('admin/', admin.site.urls),
    path('dispatch/', include('dispatch.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/profile/index', generic.RedirectView.as_view(url=reverse_lazy('index')), name='redirect-to-index')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # https://docs.djangoproject.com/en/2.2/howto/static-files/#serving-uploaded-files-in-development
