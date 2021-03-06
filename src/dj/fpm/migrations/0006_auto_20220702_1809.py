# Generated by Django 3.2.13 on 2022-07-02 18:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("fpm", "0005_dedicatedinstance_ip"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="packagedomainmap",
            name="subdomain",
        ),
        migrations.AddField(
            model_name="packagedomainmap",
            name="package",
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.CASCADE, to="fpm.package"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="packagedomainmap",
            name="state",
            field=models.CharField(
                blank=True,
                choices=[
                    ("INITIATED", "Process Initiated"),
                    ("WAITING", "SSL Certificate generation in progress"),
                    ("SUCCESS", "SSL Certificate generated sucessfully"),
                ],
                max_length=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="dedicatedinstance",
            name="status",
            field=models.CharField(
                choices=[
                    ("INITIALIZED", "Initialized"),
                    ("PENDING", "Pending"),
                    ("READY", "Ready"),
                    ("STOPPED", "Stopped"),
                    ("TERMINATED", "Terminated"),
                ],
                help_text="status of EC2 instance, ready, initialized, ect...",
                max_length=127,
            ),
        ),
    ]
