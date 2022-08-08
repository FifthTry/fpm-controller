"""proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from child_auth import views as auth_views
from child_auth import allauth_views
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth import urls
from allauth_providers.telegram import views as tg_views
from allauth_providers.discord import views as discord_views
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    re_path(
        r"^accounts/login/$", allauth_views.CustomLoginView.as_view(), name="login"
    ),
    path(
        "accounts/telegram/webhook-callback/",
        tg_views.TelegramWebhookCallback.as_view(),
        name="telegram_webhook",
    ),
    path(
        "accounts/discord/webhook-callback/",
        discord_views.DiscordWebhookCallback.as_view(),
        name="discord_bot_webhook",
    ),
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("login/callback/", auth_views.LoginCallbackView.as_view()),
    path("login/<str:provider>/", auth_views.LoginView.as_view()),
    re_path(
        r"^o/authorize/$",
        auth_views.OverrideLoginAuthorizationView.as_view(),
        name="authorize",
    ),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("get-identities/", auth_views.GetIdentity.as_view()),
    path(r"v1/fpm/", include("fpm.urls")),
]
