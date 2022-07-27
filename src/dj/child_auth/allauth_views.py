from allauth.account.views import LoginView, SignupView
from urllib.parse import parse_qsl, urlencode, urlparse
from allauth.socialaccount import providers
from django.http import HttpResponseRedirect
from django.urls import reverse


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
                    url_qs = urlencode({"process": "login", "next": next})
                    return HttpResponseRedirect(
                        f"{reverse(f'{provider_instance.id}_login')}?{url_qs}"
                    )
        return super().get(request, *args, **kwargs)
