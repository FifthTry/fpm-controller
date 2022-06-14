import django.http
from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.


def success(data, status=200):
    return JsonResponse({"result": data, "success": True}, status=status)


def error(message, status=500):
    return JsonResponse({"message": message, "success": False}, status=status)


def fpm_ready(req: django.http.HttpRequest):

    if req.method != "GET":
        return error("request method is not supported", status=402)

    ec2_reservation = req.GET.get("ec2_reservation", None)
    git_hash = req.GET.get("hash", None)

    if not ec2_reservation:
        return error("ec2_reservation is mandatory parameter", status=402)

    if not git_hash:
        return error("hash is mandatory parameter", status=402)

    return success({})


def get_package(req: django.http.HttpRequest):

    if req.method != "GET":
        return error("request method is not supported", status=402)

    ec2_reservation = req.GET.get("ec2_reservation", None)

    if not ec2_reservation:
        return error("ec2_reservation is mandatory parameter", status=402)

    return success({
        "package": "<package-name>",
        "git": "<git-url>"
    })

