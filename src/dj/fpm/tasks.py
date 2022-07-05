from huey.contrib.djhuey import task
from . import jobs as fpm_jobs

@task()
def nginx_config_generator(package_instance, server_instance):
    nginx_instance = fpm_jobs.NginxConfigGenerator(package_instance, server_instance)
    nginx_instance.generate()
