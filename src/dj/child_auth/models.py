from django.db import models
import uuid
from django.contrib.sites import models as site_models
from django.contrib.auth import get_user_model
from allauth.socialaccount import models as social_models

# from oauth2_provider import models as base_models

# class Application(base_models.AbstractApplication):
#     skip_authorization = True


class ChildWebsiteSessionId(models.Model):
    sid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    site = models.ForeignKey(site_models.Site, on_delete=models.PROTECT)


class TelegramChat(models.Model):
    chat_id = models.BigIntegerField()
    title = models.CharField(max_length=2155)
    is_active = models.BooleanField(default=False)
    # In case someone initializes the bot directly without going through the workflow(eg two different people altogether) the admin will be null
    admin = models.ForeignKey(
        social_models.SocialAccount,
        on_delete=models.CASCADE,
        help_text="This field defines maps to the SocialAccount of the user who added the Bot to the group",
        null=True,
        blank=True,
    )
