from django import forms
from fpm import models as fpm_models
from django.utils.text import slugify
from django.contrib.sites import models as site_models
from django.db import models


class PackageForm(forms.ModelForm):
    class Meta:
        model = fpm_models.Package
        fields = ("name", "plan")

    def clean_name(self):
        cleaned_data = self.clean()
        name = cleaned_data["name"]
        slug = slugify(name)
        domain = f"{slug}.5thtry.com"
        if fpm_models.Package.objects.filter(
            models.Q(name__iexact=slug) | models.Q(site__domain=domain) | models.Q(slug=slug)
        ).exists():
            self.add_error('name', "Package already exists, please use a different name")
        return name