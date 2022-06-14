from django.db import models

# Create your models here.

"""
FPM package module
"""


class Package(models.Model):
    name = models.TextField(unique=True, help_text="name of the FPM package")
    git = models.TextField(help_text="git url of FPM package")
    hash = models.TextField(null=True, blank=True, help_text="latest deployed hash of git")
    plan = models.TextField(help_text="We have different plans like free, paid for serving FPM package")
    hours = models.IntegerField(default=0)
    status = models.TextField(help_text="status of the package")


class DedicatedInstance(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    ec2_reservation = models.TextField(db_index=True)
    ec2_instance_id = models.TextField(null=True, blank=True)
    status = models.TextField(help_text="status of EC2 instance, ready, initializing, ect...")
