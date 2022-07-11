from django.contrib import admin
from fpm import models as fpm_models


@admin.register(fpm_models.Plan)
class PlanAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "hours_per_day")


@admin.action(description="Turn off package instances")
def stop_package_instances(modeladmin, request, queryset):
    queryset.update(status="p")


@admin.register(fpm_models.Package)
class PackageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "plan", "status", "is_running")
    exclude = ("created_at", "updated_at", "status")
    actions = [stop_package_instances]

    def is_running(self, instance):
        return True


@admin.register(fpm_models.PackageDomainMap)
class PackageDomainMapAdmin(admin.ModelAdmin):
    list_display = ("package", "custom_domain")


admin.site.register(fpm_models.DedicatedInstance)
admin.site.register(fpm_models.PackageDeployment)
