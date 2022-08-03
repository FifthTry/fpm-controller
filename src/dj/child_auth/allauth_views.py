from allauth.account.views import LoginView, SignupView
from urllib.parse import parse_qsl, urlencode, urlparse
from allauth.socialaccount import providers
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.template.response import TemplateResponse
from django.conf import settings


class CustomLoginView(LoginView):
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
        return super().get(request, *args, **kwargs)


def socialaccount_str(instance):
    return ""
