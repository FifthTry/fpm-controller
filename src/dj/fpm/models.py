from django.db import models

# Create your models here.

package_status = [
    ("deployed", "Package Deployed"),
    ("in_dev", "In development state")
]

instance_status = [
    ("initializing", "Instance Initializing"),
    ("ready", "Instance ready to serve"),
    ("failed", "Failed to initialize")
]


class Package(models.Model):
    name = models.CharField(unique=True, help_text="name of the FPM package", max_length=255)
    git = models.CharField(help_text="git url of FPM package", max_length=1023)
    hash = models.CharField(null=True, blank=True, help_text="latest deployed hash of git", max_length=512)
    plan = models.CharField(help_text="We have different plans like free, paid for serving FPM package", max_length=255)
    hours = models.IntegerField(default=0)
    status = models.CharField(help_text="status of the package", max_length=255, choices=package_status)


class DedicatedInstance(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    ec2_reservation = models.CharField(db_index=True, max_length=255)
    ec2_instance_id = models.CharField(null=True, blank=True, max_length=255)
    status = models.CharField(
        help_text="status of EC2 instance, ready, initializing, ect...", max_length=127, choices=instance_status)
