import ftd
import ftd_django
from django.template.backends.utils import csrf_token_lazy
from fpm import models as fpm_models


@ftd_django.processor("csrf_token")
def csrf_token(request, doc_id, section, interpreter):
    # ftd.object_to_value({}, section, interpreter)
    return ftd.string_to_value(str(csrf_token_lazy(request)))


@ftd_django.processor("deployed_projects")
def deployed_projects(request, doc_id, section, interpreter):
    # ftd.object_to_value({}, section, interpreter)
    data = []
    for instance in fpm_models.Package.objects.filter(owner=request.user):
        data.append({"name": instance.name, "url": f"https://{instance.site.domain}"})
    return ftd.object_to_value(data, section, interpreter)
