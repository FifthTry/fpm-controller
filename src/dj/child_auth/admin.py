from django.contrib import admin
from .models import TelegramChat, ChildWebsiteSessionId

# Register your models here.
admin.site.register(TelegramChat)
admin.site.register(ChildWebsiteSessionId)
