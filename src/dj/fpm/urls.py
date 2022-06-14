from django.urls import path

from . import views

urlpatterns = [
    path(r"dev/fpm-ready", views.fpm_ready),
    path(r"dev/get-package", views.get_package)
]
