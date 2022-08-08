import requests

from allauth.socialaccount.providers.discord.provider import DiscordProvider
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.views.generic import View
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from nacl.signing import VerifyKey
from allauth.socialaccount import app_settings
import logging
from . import models as discord_models

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


class DiscordOAuth2Adapter(OAuth2Adapter):
    provider_id = DiscordProvider.id
    access_token_url = "https://discord.com/api/oauth2/token"
    authorize_url = "https://discord.com/api/oauth2/authorize"
    profile_url = "https://discord.com/api/users/@me"

    def complete_login(self, request, app, token, **kwargs):
        headers = {
            "Authorization": "Bearer {0}".format(token.token),
            "Content-Type": "application/json",
        }
        extra_data = requests.get(self.profile_url, headers=headers)
        resp = self.get_provider().sociallogin_from_response(request, extra_data.json())
        guild_instance = kwargs.get("response", {}).get("guild", None)
        if guild_instance:
            (guild, _) = discord_models.DiscordBotInstallation.objects.update_or_create(
                guild_id=guild_instance["id"],
            )
            for role in guild_instance["roles"]:
                discord_models.GuildRoleMap.objects.update_or_create(
                    role_id=role["id"],
                    guild=guild,
                    defaults={"role_name": role["name"]},
                )
        return resp


oauth2_login = OAuth2LoginView.adapter_view(DiscordOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(DiscordOAuth2Adapter)


class DiscordWebhookCallback(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @classmethod
    def verify_key(
        cls, raw_body: str, signature: str, timestamp: str, client_public_key: str
    ):
        message = timestamp.encode() + raw_body
        try:
            vk = VerifyKey(bytes.fromhex(client_public_key))
            vk.verify(message, bytes.fromhex(signature))
            return True
        except Exception as ex:
            print(ex)
            pass
        return False

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        # provider = providers.registry.by_id("discord", request)
        settings = app_settings.PROVIDERS.get("discord", {})
        data = json.loads(request.body)
        logger.error(data)

        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        if not DiscordWebhookCallback.verify_key(
            request.body, signature, timestamp, settings["INTERACTIONS_PUBLIC_KEY"]
        ):
            return HttpResponse("Bad request signature", status=401)
        logger.error(data)
        return JsonResponse(data)
