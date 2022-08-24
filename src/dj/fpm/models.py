from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator

# import fpm import lib
from fpm import jobs as fpm_jobs
from tempfile import NamedTemporaryFile
from django.conf import settings
from textwrap import dedent
from django.utils.text import slugify
import subprocess
from fpm import tasks
from django.contrib.sites import models as site_models
from oauth2_provider.models import Application
from django.conf import settings
from django.db import transaction

instance_status = [
    ("initializing", "Instance Initializing"),
    ("ready", "Instance ready to serve"),
    ("failed", "Failed to initialize"),
]


class Plan(models.Model):
    name = models.CharField(
        max_length=50,
    )
    slug = models.SlugField(max_length=50, unique=True)
    hours_per_day = models.IntegerField(
        default=24, validators=[MaxValueValidator(24), MinValueValidator(1)]
    )

    def __str__(self) -> str:
        return f"{self.name} [{self.hours_per_day} hours per day]"


class Package(models.Model):
    class PackageStatusChoices(models.TextChoices):
        CONNECTED = "CONNECTED", "Connected"
        DEPLOYED = "DEPLOYED", "Deployed"
        ARCHIVED = "ARCHIVED", "Archived"

    class DomainMapStatusChoices(models.TextChoices):
        INITIATED = "INITIATED", "Process Initiated"
        WAITING = "WAITING", "SSL Certificate generation in progress"
        FAILED = "FAILED", "SSL Certificate generation failed"
        SUCCESS = "SUCCESS", "SSL Certificate generated sucessfully"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(
        unique=True, help_text="name of the FPM package", max_length=255
    )
    slug = models.SlugField(max_length=50, unique=True)
    git = models.CharField(
        help_text="git url of FPM package",
        max_length=1023,
        validators=[
            RegexValidator(
                regex=r"((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?",
                message="Please enter a valid git url",
            )
        ],
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        help_text="We have different plans like free, paid for serving FPM package",
    )
    status = models.CharField(
        help_text="status of the package",
        max_length=20,
        choices=PackageStatusChoices.choices,
        default=PackageStatusChoices.CONNECTED,
        editable=False
    )
    site = models.OneToOneField(site_models.Site, on_delete=models.PROTECT)
    domain_state = models.CharField(
        choices=DomainMapStatusChoices.choices, max_length=10, null=True, blank=True
    )
    application = models.OneToOneField(Application, on_delete=models.PROTECT)
    app_secret = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs) -> None:
        if self.pk is None:
            self.domain_state = self.DomainMapStatusChoices.INITIATED
            self.application = Application()
            self.app_secret = self.application.client_secret
        application = self.application
        application.name = self.name
        application.skip_authorization = True
        application.client_type = Application.CLIENT_PUBLIC
        application.authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
        with transaction.atomic():
            (self.site, _) = site_models.Site.objects.get_or_create(
                name=self.name, domain=f"{self.slug}.5thtry.com"
            )
            application.redirect_uris = f"https://{self.site.domain}/-/dj/login/callback/"
            application.save()
            super().save(*args, **kwargs)
            self.refresh_from_db()
        (server_instance, is_new) = DedicatedInstance.objects.get_or_create(
            package=self,
        )
        if is_new:
            server_instance.initialize()
        if self.domain_state != self.DomainMapStatusChoices.SUCCESS:
            nginx_config_instance = tasks.nginx_config_generator(
                self, self.dedicatedinstance_set.get()
            )
            nginx_config_instance()


class PackageDomainMap(models.Model):
    class DomainMapStatusChoices(models.TextChoices):
        INITIATED = "INITIATED", "Process Initiated"
        WAITING = "WAITING", "SSL Certificate generation in progress"
        FAILED = "FAILED", "SSL Certificate generation failed"
        SUCCESS = "SUCCESS", "SSL Certificate generated sucessfully"

    package = models.ForeignKey(
        Package, on_delete=models.CASCADE, related_name="domains"
    )
    # Domain is unique. Including a subdomain
    custom_domain = models.CharField(max_length=100, null=True, blank=True, unique=True)
    state = models.CharField(
        choices=DomainMapStatusChoices.choices, max_length=10, null=True, blank=True
    )

    def __str__(self) -> str:
        return f"{self.custom_domain} - {self.package.name}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.state = self.DomainMapStatusChoices.INITIATED
        # if self.pk is not None and self.state in [self.DomainMapStatusChoices.WAITING]:
        #     assert False, "Panic! Waiting for the task to complete"
        super().save(*args, **kwargs)
        if self.state != self.DomainMapStatusChoices.SUCCESS:
            nginx_config_instance = tasks.nginx_config_generator(
                self.package, self.package.dedicatedinstance_set.get()
            )
            nginx_config_instance()
            # nginx_config_instance = fpm_jobs.NginxConfigGenerator(
            #     self.package, self.package.dedicatedinstance_set.get()
            # )
            # nginx_config_instance.generate()


class DedicatedInstance(models.Model):
    class InstanceStatus(models.TextChoices):
        INITIALIZED = "INITIALIZED", "Initialized"
        PENDING = "PENDING", "Pending"
        READY = "READY", "Ready"
        STOPPED = "STOPPED", "Stopped"
        TERMINATED = "TERMINATED", "Terminated"

    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    ec2_instance_id = models.CharField(db_index=True, unique=True, max_length=30)
    status = models.CharField(
        help_text="status of EC2 instance, ready, initialized, ect...",
        max_length=127,
        choices=InstanceStatus.choices,
    )
    ip = models.GenericIPAddressField(blank=True, null=True)
    config = models.FileField(upload_to="confs", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.package.name} {self.ec2_instance_id} @ {self.ip}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.status = self.InstanceStatus.INITIALIZED
        super().save(*args, **kwargs)

    def initialize(self):
        client_manager = fpm_jobs.ClientManager()
        (self.ec2_instance_id, self.ip) = client_manager.create_instance(
            self.package.name
        )
        self.status = self.InstanceStatus.PENDING
        self.save()


class PackageDeployment(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    hash = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
