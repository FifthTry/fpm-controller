from django.contrib import admin
from .models import DiscordBotInstallation, GuildRoleMap

# Register your models here.
admin.site.register(DiscordBotInstallation)
admin.site.register(GuildRoleMap)
