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
from django.http import HttpResponseRedirect, JsonResponse
from django.views import View

from .provider import TelegramProvider
from django.views.decorators.csrf import csrf_exempt
from child_auth.models import TelegramChat
from allauth.socialaccount import models as social_models
from django.template.response import TemplateResponse
from urllib.parse import urlencode
from django.conf import settings
from allauth.socialaccount.providers.base import AuthProcess


def telegram_login(request):
    provider = providers.registry.by_id(TelegramProvider.id, request)
    data = dict(request.GET.items())
    if data.get("process") == "connect" and data.get("hash") is None:
        next = data.get("next")
        callback_url = f"https://5thtry.com/accounts/telegram/login/?" + urlencode(
            {"next": next, "process": "connect"}
        )
        return TemplateResponse(
            request,
            "telegram_login.html",
            {
                "callback_url": callback_url,
                "bot_name": settings.SOCIALACCOUNT_PROVIDERS["telegram"]["BOT_NAME"],
            },
        )

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
    if data.get("next"):
        login.state["next"] = data["next"]
    if data.get("process") == "connect":
        login.state["process"] = AuthProcess.CONNECT
    return complete_social_login(request, login)


class TelegramWebhookCallback(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        response = {}
        # Check for the self's addition/removal query
        add_remove_data = data.get("my_chat_member")
        if add_remove_data:
            try:
                new_status = add_remove_data.get("new_chat_member", {})["status"]
                is_active = not (new_status == "left")
            except KeyError:
                pass
            else:
                (instance, _) = TelegramChat.objects.update_or_create(
                    chat_id=add_remove_data["chat"]["id"],
                    admin=social_models.SocialAccount.objects.filter(
                        provider="telegram", uid=add_remove_data["from"]["id"]
                    ).first(),
                    defaults={
                        "is_active": is_active,
                        "title": add_remove_data["chat"]["title"],
                    },
                )
                if is_active:
                    response["method"] = "sendMessage"
                    response["chat_id"] = instance.chat_id
                    response[
                        "text"
                    ] = f"Thank you for installing FifthtryBot! Your chat ID is {instance.chat_id}"
        return JsonResponse(response)
