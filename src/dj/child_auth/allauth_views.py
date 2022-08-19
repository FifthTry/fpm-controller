import json
from allauth.account.views import LoginView, SignupView
from urllib.parse import parse_qsl, urlencode, urlparse
from allauth.socialaccount import providers
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.template.response import TemplateResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class CustomLoginView(LoginView):
    template_name = "/sign-in/"

    def get(self, request, *args, **kwargs):
        next = request.GET.get("next") or None
        if next:
            url = urlparse(next)
            if url.path == "/o/authorize/":
                query = dict(parse_qsl(url.query))
                provider = query.get("provider") or None
                if provider:
                    provider_instance = providers.registry.by_id(provider)
                    if provider == "telegram":
                        callback_url = (
                            f"https://5thtry.com/accounts/telegram/login/?"
                            + urlencode({"next": next})
                        )
                        return TemplateResponse(
                            request,
                            "telegram_login.html",
                            {
                                "callback_url": callback_url,
                                "bot_name": settings.SOCIALACCOUNT_PROVIDERS[
                                    "telegram"
                                ]["BOT_NAME"],
                            },
                        )
                    else:
                        url_qs = urlencode({"process": "login", "next": next})
                    return HttpResponseRedirect(
                        f"{reverse(f'{provider_instance.id}_login')}?{url_qs}"
                    )
        else:
            return self.render_to_response({})
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        body = request.body.decode("utf-8")
        json_body = json.loads(body)
        form_class = self.get_form_class()
        form = form_class(json_body, request=request)
        if form.is_valid():
            response = self.form_valid(form)
            resp = JsonResponse({"redirect": "/"})
            resp.cookies = response.cookies
        else:
            resp = JsonResponse({k: [x for x in v] for (k, v) in form.errors.items()})
        return resp


def socialaccount_str(instance):
    return ""


@method_decorator(csrf_exempt, name="dispatch")
class CustomSignUpView(SignupView):
    template_name = "/sign-up/"

    def get_context_data(self, **kwargs):
        return {}

    def post(self, request, *args, **kwargs):
        body = request.body.decode("utf-8")
        json_body = json.loads(body)
        form_class = self.get_form_class()
        form = form_class(json_body)
        if form.is_valid():
            original_resp = self.form_valid(form)
            resp = JsonResponse({})
            resp.cookies = original_resp.cookies
        else:
            resp = JsonResponse({k: [x for x in v] for (k, v) in form.errors.items()})
        return resp
