from django.urls import path

from . import views

urlpatterns = [
    path("dev/fpm-ready", views.fpm_ready),
    path("dev/get-package", views.get_package)
]
