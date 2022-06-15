from django.contrib import admin
from fpm.models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "hours", "status")
    exclude = ("created_at", "updated_at")
