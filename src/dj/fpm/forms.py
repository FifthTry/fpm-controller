from django import forms
from fpm import models as fpm_models


class PackageForm(forms.ModelForm):
    class Meta:
        model = fpm_models.Package
        fields = ("name", "plan")
