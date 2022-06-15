from django.urls import path

from . import views

urlpatterns = [
    path(r"fpm-ready", views.fpm_ready),
    path(r"get-package", views.get_package),
]
