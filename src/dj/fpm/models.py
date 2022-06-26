from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
# import fpm import lib
from fpm import jobs as fpm_jobs
from tempfile import NamedTemporaryFile
from django.conf import settings
from textwrap import dedent
from django.utils.text import slugify
import subprocess


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
        server_instance = DedicatedInstance.objects.get_or_create(
            package=self,
        )


class PackageDomainMap(models.Model):
    subdomain = models.SlugField(max_length=50, unique=True)
    custom_domain = models.CharField(max_length=100, null=True, blank=True)


class DedicatedInstance(models.Model):
    class InstanceStatus(models.TextChoices):
        INITIALIZING = "INITIALIZING", "Initializing"
        READY = "READY", "Ready"
        STOP = "STOPPED", "Stopped"


    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    ec2_instance_id = models.CharField(db_index=True, unique=True, max_length=30)
    status = models.CharField(
        help_text="status of EC2 instance, ready, initializing, ect...",
        max_length=127,
        choices=InstanceStatus.choices,
    )
    ip = models.GenericIPAddressField(blank=True, null=True)
    config = models.FileField(upload_to="confs", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        client_manager = fpm_jobs.ClientManager()
        if self.pk is None:
            self.status = "initializing"
            (self.ec2_instance_id, self.ip) = client_manager.create_instance()
        # elif self.status == self.InstanceStatus.STOP:
        #     client_manager.stop_instance(self.ec2_instance_id)
        super().save(*args, **kwargs)
    
    def mark_ready(self, git_hash):
        # Create the nginx config
        # Save the nginx config
        # Reload the nginx configurations
        # with open(settings.NGINX_CONFIG_DIR + "")
        # print()
        with open(settings.NGINX_CONFIG_DIR + f"{self.package.id}.conf", "w+") as f:
            f.write(dedent("""
            server {
                listen       80;
                listen       [::]:80;
                server_name %s.5thtry.com;
                location / {
                    proxy_pass http://%s:8000;
                }
            }
            """ %(self.package.name, self.ip))
            )
        subprocess.run(["sudo", "systemctl", "restart", "nginx"])
        self.status = self.InstanceStatus.READY
        self.save()
        pass


class PackageDeployment(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    hash = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
