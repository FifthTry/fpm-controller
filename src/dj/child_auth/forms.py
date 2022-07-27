from django import forms

PROVIDER_CHOICES = (("github", "GitHub"),)


class LoginWithFifthtryForm(forms.Form):
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    provider = forms.ChoiceField(choices=PROVIDER_CHOICES)
