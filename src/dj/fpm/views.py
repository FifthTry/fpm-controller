import json
import django.http
from django.http import JsonResponse, HttpResponseRedirect
from fpm import models as fpm_models
from fpm import jobs as fpm_jobs
from fpm import tasks as fpm_tasks
from django.views.generic import TemplateView, FormView
from fpm import forms as fpm_forms


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
        instance: fpm_models.DedicatedInstance = (
            fpm_models.DedicatedInstance.objects.get(ec2_instance_id=ec2_instance_id)
        )
    except:
        return error("instance with ec2_instance_id id not found", status=404)
    # instance.package.hash = git_hash
    nginx_config_manager = fpm_tasks.nginx_config_generator(instance.package, instance)
    nginx_config_manager()
    # nginx_config_manager = fpm_jobs.NginxConfigGenerator(instance.package, instance)
    # nginx_config_manager.generate()
    instance.status = fpm_models.DedicatedInstance.InstanceStatus.READY
    instance.save()

    return success({})


def get_package(req: django.http.HttpRequest):
    if req.method != "GET":
        return error("request method is not supported", status=402)

    ec2_instance_id = req.GET.get("ec2_instance_id", None)

    if not ec2_instance_id:
        return error("ec2_instance_id is mandatory parameter", status=402)

    try:
        instance: fpm_models.DedicatedInstance = (
            fpm_models.DedicatedInstance.objects.get(ec2_instance_id=ec2_instance_id)
        )
    except:
        return error("instance with ec2_instance_id id not found", status=404)

    return success(
        {
            "package": instance.package.name,
            "git": instance.package.git,
            "base": "https://github.com/",
        }
    )


class IndexView(TemplateView):
    template_name = "/dashboard/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/accounts/login/")
        return super().dispatch(request, *args, **kwargs)


from django.utils.text import slugify

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class CreateNewView(TemplateView):
    template_name: str = "/create-package/"
    form_class = fpm_forms.PackageForm
    # success_url = "/"

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        form_instance = fpm_forms.PackageForm(data)
        if not form_instance.is_valid():
            mapped_keys = {
                "name": "fifthtry.github.io/fpm-controller-ui/create-package/#error-package-name",
                "plan": "fifthtry.github.io/fpm-controller-ui/create-package/#error-plan",
                "__all__": "fifthtry.github.io/fpm-controller-ui/create-package/#error-form",
            }
            return JsonResponse(
                {
                    "data": {
                        mapped_keys[k]: ", ".join([x for x in v])
                        for (k, v) in form_instance.errors.items()
                    }
                }
            )
        else:
            instance = form_instance.save(commit=False)
            instance.slug = slugify(instance.name)
            instance.owner = self.request.user
            instance.save()
        return JsonResponse({"data": {"url": "/"}})
