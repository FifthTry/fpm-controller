import json
import hashlib
import hmac
import time
from django.utils.decorators import method_decorator

from allauth.socialaccount import providers
from allauth.socialaccount.helpers import (
    complete_social_login,
    render_authentication_error,
)
from django.http import JsonResponse
from django.views import View

from .provider import TelegramProvider
from django.views.decorators.csrf import csrf_exempt
from child_auth.models import TelegramChat
from allauth.socialaccount import models as social_models


def telegram_login(request):
    provider = providers.registry.by_id(TelegramProvider.id, request)
    data = dict(request.GET.items())
    hash = data.pop("hash")
    payload = "\n".join(sorted(["{}={}".format(k, v) for k, v in data.items()]))
    token = provider.get_settings()["TOKEN"]
    token_sha256 = hashlib.sha256(token.encode()).digest()
    expected_hash = hmac.new(token_sha256, payload.encode(), hashlib.sha256).hexdigest()
    auth_date = int(data.pop("auth_date"))
    if time.time() - auth_date > 30:
        return render_authentication_error(
            request, provider_id=provider.id, extra_context={"response": data}
        )

    login = provider.sociallogin_from_response(request, data)
    return complete_social_login(request, login)


class TelegramWebhookCallback(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        # Check for the self's addition/removal query
        add_remove_data = data.get("my_chat_member")
        if add_remove_data:
            try:
                new_status = add_remove_data.get("new_chat_member", {})["status"]
                is_active = not (new_status == "left")
            except KeyError:
                pass
            else:
                TelegramChat.objects.update_or_create(
                    chat_id=add_remove_data["chat"]["id"],
                    admin=social_models.SocialAccount.objects.filter(
                        provider="telegram", uid=add_remove_data["from"]["id"]
                    ).first(),
                    defaults={
                        "is_active": is_active,
                        "title": add_remove_data["chat"]["title"],
                    },
                )
        return JsonResponse({})
