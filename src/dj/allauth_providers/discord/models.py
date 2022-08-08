from django.db import models
from haikunator import Haikunator
from allauth.socialaccount import models as social_models

haikunator_instance = Haikunator()


def generate_chat_name():
    return haikunator_instance.haikunate(token_length=0)


class DiscordBotInstallation(models.Model):
    guild_id = models.BigIntegerField()
    user_friendly_name = models.CharField(
        unique=True, default=generate_chat_name, max_length=50
    )
    admin = models.ForeignKey(
        social_models.SocialAccount,
        on_delete=models.CASCADE,
        help_text="This field defines maps to the SocialAccount of the user who added the Bot to the guild",
        null=True,
        blank=True,
    )


class GuildRoleMap(models.Model):
    guild = models.ForeignKey(DiscordBotInstallation, on_delete=models.CASCADE)
    role_name = models.CharField(max_length=100)
    role_id = models.BigIntegerField()

    class Meta:
        unique_together = ("role_id", "guild")
