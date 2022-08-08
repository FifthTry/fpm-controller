from django.views.generic import View
from django.http import JsonResponse


class DiscordWebhookCallback(View):
    def post(self, request, *args, **kwargs):
        return JsonResponse({})
