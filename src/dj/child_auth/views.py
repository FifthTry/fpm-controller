from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.views import View
from django.views.generic import TemplateView, FormView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from . import forms as app_forms
from django.contrib.sites.shortcuts import get_current_site
import pkce
import urllib.parse
import requests

from allauth.socialaccount import providers
from urllib.parse import urlencode

from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.models import get_application_model, get_access_token_model
import json
from django.utils import timezone
from oauth2_provider.views.base import AuthorizationView


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(FormView):
    template_name = "sister_site_login.html"
    form_class = app_forms.LoginWithFifthtryForm

    def get_initial(self):
        return {"next": self.request.GET.get("next") or ""}

    def form_valid(self, form):
        data = form.data
        self.next = data.get("next") or None
        self.provider = data["provider"]
        return super().form_valid(form)

    def get_success_url(self):
        site = get_current_site(self.request)
        current_package = site.package
        oauth_application = current_package.application
        code_verifier, code_challenge = pkce.generate_pkce_pair()
        url = f"{settings.BASE_SITE_DOMAIN}/o/authorize?"
        params = {
            "client_id": oauth_application.client_id,
            "response_type": "code",
            "code_challenge": code_challenge,
            "provider": self.provider,
            "redirect_uri": f"https://{site.domain}/-/dj/login/callback/",
        }
        self.request.session["code_verifier"] = code_verifier
        self.request.session["post_login_url"] = self.next
        self.request.session.modified = True
        return url + urllib.parse.urlencode(params)


class LoginCallbackView(View):
    def get(self, request, *args, **kwargs):
        # TODO: GET ID AND SECRET FOR CURRENT SITE
        site = get_current_site(self.request)
        current_package = site.package
        oauth_application = current_package.application
        code = request.GET["code"]
        data = {
            "client_id": oauth_application.client_id,
            "client_secret": current_package.app_secret,
            "code": code,
            "grant_type": "authorization_code",
            "code_verifier": pkce.get_code_challenge(
                self.request.session.pop("code_verifier")
            ),
            "redirect_uri": f"https://{site.domain}/-/dj/login/callback/",
        }
        # TODO: Migrate to fifthtry.com from settings
        resp = requests.post(
            f"{settings.BASE_SITE_DOMAIN}/o/token/",
            data=data,
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response = JsonResponse({"success": resp.ok, "data": data, "resp": resp.json()})
        if resp.ok:
            response.set_cookie("cookie_name", "cookie_value")
            # self.request.session.modified = True
        return response
        # return super().get(request, *args, **kwargs)


class GetIdentity(View):
    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("sid") or None
        if session_id is None:
            return JsonResponse(
                {"success": False, "reason": "`sid` not found in request"}, status=400
            )
        resp = {
            "success": True,
            "user-identities": [{"email": "yo@y.com"}, {"github": "foo"}],
        }
        return JsonResponse(resp)


class OverrideLoginAuthorizationView(AuthorizationView):
    def get(self, request, *args, **kwargs):

        try:
            provider_instance = providers.registry.by_id(request.GET["provider"])
        except KeyError:
            return HttpResponseBadRequest()
        existing_accounts = request.user.socialaccount_set.filter(
            provider=provider_instance.id
        )
        if not existing_accounts.exists():
            next = f"{request.path}?{request.GET.urlencode()}"
            url_qs = urlencode({"process": "connect", "next": next})
            # Here the user should be connected and the next should be set to authorize URL
            return HttpResponseRedirect(
                f"{reverse(f'{provider_instance.id}_login')}?{url_qs}"
            )
        return super().get(request, *args, **kwargs)
