from django.db import models
import uuid
from django.contrib.sites import models as site_models
from django.contrib.auth import get_user_model

# from oauth2_provider import models as base_models

# class Application(base_models.AbstractApplication):
#     skip_authorization = True


class ChildWebsiteSessionId(models.Model):
    sid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    site = models.ForeignKey(site_models.Site, on_delete=models.PROTECT)
