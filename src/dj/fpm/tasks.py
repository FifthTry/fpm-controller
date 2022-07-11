from huey.contrib.djhuey import task
from . import jobs as fpm_jobs
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@task()
def nginx_config_generator(package_instance, server_instance):
    logger.debug(f"Recieved request for {package_instance.slug}")
    nginx_instance = fpm_jobs.NginxConfigGenerator(package_instance, server_instance)
    nginx_instance.generate()
