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
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.refresh_from_db()
        (server_instance, is_new) = DedicatedInstance.objects.get_or_create(
            package=self,
        )
        if is_new:
            server_instance.initialize()


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
        if self.pk is not None and self.state in [self.DomainMapStatusChoices.WAITING]:
            assert False, "Panic! Waiting for the task to complete"
        super().save(*args, **kwargs)
        if self.state != self.DomainMapStatusChoices.SUCCESS:
            nginx_config_instance = tasks.nginx_config_generator(
                self.package,
                self.package.dedicatedinstance_set.get()
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

    def mark_ready(self, git_hash):
        with open(settings.NGINX_CONFIG_DIR + f"{self.package.id}.conf", "w+") as f:
            f.write(
                dedent(
                    """
            server {
                listen       80;
                listen       [::]:80;
                server_name %s.5thtry.com;
                location / {
                    proxy_pass http://%s:8000;
                    proxy_http_version 1.1;
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_buffering off;
                }
            }
            """
                    % (slugify(self.package.slug), self.ip)
                )
            )
        subprocess.Popen(
            ["sudo /bin/systemctl restart nginx"],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.status = self.InstanceStatus.READY
        self.save()


class PackageDeployment(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    hash = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
