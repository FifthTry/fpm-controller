import django.http
from django.http import JsonResponse
from fpm.models import DedicatedInstance
from fpm import jobs as fpm_jobs


def success(data, status=200):
    return JsonResponse({"result": data, "success": True}, status=status)


def error(message, status=500):
    return JsonResponse({"message": message, "success": False}, status=status)


def fpm_ready(req: django.http.HttpRequest):

    if req.method != "GET":
        return error("request method is not supported", status=402)

    ec2_instance_id = req.GET.get("ec2_instance_id", None)
    git_hash = req.GET.get("hash", None)

    if not ec2_instance_id:
        return error("ec2_instance_id is mandatory parameter", status=402)

    if not git_hash:
        return error("hash is mandatory parameter", status=402)

    try:
        instance: DedicatedInstance = DedicatedInstance.objects.get(
            ec2_instance_id=ec2_instance_id
        )
    except:
        return error("instance with ec2_instance_id id not found", status=404)
    # instance.package.hash = git_hash
    nginx_config_manager = fpm_jobs.NginxConfigGenerator(instance.package, instance)
    nginx_config_manager.generate()
    instance.status = DedicatedInstance.InstanceStatus.READY
    instance.save()

    return success({})


def get_package(req: django.http.HttpRequest):
    if req.method != "GET":
        return error("request method is not supported", status=402)

    ec2_instance_id = req.GET.get("ec2_instance_id", None)

    if not ec2_instance_id:
        return error("ec2_instance_id is mandatory parameter", status=402)

    try:
        instance: DedicatedInstance = DedicatedInstance.objects.get(
            ec2_instance_id=ec2_instance_id
        )
    except:
        return error("instance with ec2_instance_id id not found", status=404)

    # return success({"package": "inter", "git": instance.package.git, "base": "https://fifthtry.com/"})
    return success(
        {
            "package": instance.package.name,
            "git": instance.package.git,
            "base": "https://github.com/",
        }
    )
