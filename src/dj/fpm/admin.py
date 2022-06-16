from django.contrib import admin
from fpm import models as fpm_models


@admin.register(fpm_models.Plan)
class PlanAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "hours_per_day")


@admin.register(fpm_models.Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "status")
    exclude = ("created_at", "updated_at", "status")
