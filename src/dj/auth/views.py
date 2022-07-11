from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    def post(self, request, *args, **kwargs):
        assert False, request


class GetIdentity(View):
    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("sid") or None
        if session_id is None:
            return JsonResponse(
                {"success": False, "reason": "`sid` not found in request"}
            )
        resp = {
            "success": True,
            "user-identities": [{"email": "yo@y.com"}, {"github": "foo"}],
        }
        return JsonResponse(resp)
