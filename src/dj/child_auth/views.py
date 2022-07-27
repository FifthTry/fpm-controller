from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.conf import settings
from django.views import View
from django.views.generic import TemplateView, FormView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from . import forms as app_forms
from . import models as child_auth_models
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
from allauth.socialaccount.helpers import socialaccount_user_display


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    def get(self, request, provider, *args, **kwargs):
        site = get_current_site(self.request)
        current_package = site.package
        oauth_application = current_package.application
        code_verifier, code_challenge = pkce.generate_pkce_pair()
        url = f"{settings.BASE_SITE_DOMAIN}/o/authorize?"
        next_url = request.META.get("HTTP_REFERER", f"https://{site.domain}/")
        params = {
            "client_id": oauth_application.client_id,
            "response_type": "code",
            "code_challenge": code_challenge,
            "provider": provider,
            "redirect_uri": f"https://{site.domain}/-/dj/login/callback/?next={next_url}",
        }
        self.request.session["code_verifier"] = code_verifier
        self.request.session.modified = True
        return HttpResponseRedirect(url + urllib.parse.urlencode(params))


class LoginCallbackView(View):
    def get(self, request, *args, **kwargs):
        # TODO: GET ID AND SECRET FOR CURRENT SITE
        site = get_current_site(self.request)
        current_package = site.package
        oauth_application = current_package.application
        code = request.GET["code"]
        next = request.GET.get("next") or f"https://{site.domain}/"
        data = {
            "client_id": oauth_application.client_id,
            "client_secret": current_package.app_secret,
            "code": code,
            "grant_type": "authorization_code",
            "code_verifier": pkce.get_code_challenge(
                self.request.session.pop("code_verifier")
            ),
            "redirect_uri": f"https://{site.domain}/-/dj/login/callback/?next={next}",
        }
        resp = requests.post(
            f"{settings.BASE_SITE_DOMAIN}/o/token/",
            data=data,
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if resp.ok:
            resp_data = resp.json()
            access_token_instance = get_access_token_model().objects.get(
                token=resp_data["access_token"]
            )
            session_instance = child_auth_models.ChildWebsiteSessionId.objects.create(
                user=access_token_instance.user, site=site
            )
            response = HttpResponseRedirect(next)
            response.set_cookie("sid", session_instance.sid)
        else:
            response = HttpResponseBadRequest(resp.text)
        return response


from github import Github


class GetIdentity(View):
    @classmethod
    def resolve_github_like(cls, user, repo_name) -> bool:
        github_accounts = user.socialaccount_set.filter(provider="github")
        for github_account in github_accounts:
            github_instance = Github(
                github_account.socialtoken_set.latest("expires_at").token
            )
            is_starred = github_instance.get_user().has_in_starred(
                github_instance.get_repo(repo_name)
            )
            if is_starred:
                return is_starred
        return False

    @classmethod
    def resolve_github_contributor(cls, user, repo_name) -> bool:
        github_accounts = user.socialaccount_set.filter(provider="github")
        for github_account in github_accounts:
            try:
                github_instance = Github(
                    github_account.socialtoken_set.latest("expires_at").token
                )
                is_contributor = any(
                    [
                        contributor.login == github_instance.get_user().login
                        for contributor in github_instance.get_repo(
                            repo_name
                        ).get_contributors()
                    ]
                )
                if is_contributor:
                    return is_contributor
            except:
                pass
        return False

    @classmethod
    def resolve_github_watch(cls, user, repo_name) -> bool:
        github_accounts = user.socialaccount_set.filter(provider="github")
        for github_account in github_accounts:
            github_instance = Github(
                github_account.socialtoken_set.latest("expires_at").token
            )
            has_in_watched = github_instance.get_user().has_in_watched(
                github_instance.get_repo(repo_name)
            )
            if has_in_watched:
                return has_in_watched
        return False

    def evaluate_secondary_identities(self, request, session, *args, **kwargs):
        req_params = request.GET.dict()
        req_params.pop("sid")
        resp = list()
        for (key, value) in req_params.items():
            fn_name = f"resolve_{key.replace('-', '_')}"
            if hasattr(GetIdentity, fn_name) and getattr(GetIdentity, fn_name)(
                session.user, value
            ):
                resp.append({key: value})
        return resp

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("sid") or None
        if session_id is None:
            return JsonResponse(
                {"success": False, "reason": "`sid` not found in request"}, status=400
            )
        session_instance = get_object_or_404(
            child_auth_models.ChildWebsiteSessionId, sid=session_id
        )
        resp = {
            "success": True,
            "user-identities": [
                {social_account.provider: socialaccount_user_display(social_account)}
                for social_account in session_instance.user.socialaccount_set.all()
            ]
            + self.evaluate_secondary_identities(
                request, session_instance, args, kwargs
            ),
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
            return HttpResponseRedirect(
                f"{reverse(f'{provider_instance.id}_login')}?{url_qs}"
            )
        return super().get(request, *args, **kwargs)
