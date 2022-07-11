# Generated by Django 3.2.13 on 2022-07-03 05:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fpm", "0006_auto_20220702_1809"),
    ]

    operations = [
        migrations.AlterField(
            model_name="packagedomainmap",
            name="custom_domain",
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="packagedomainmap",
            name="state",
            field=models.CharField(
                blank=True,
                choices=[
                    ("INITIATED", "Process Initiated"),
                    ("WAITING", "SSL Certificate generation in progress"),
                    ("FAILED", "SSL Certificate generation failed"),
                    ("SUCCESS", "SSL Certificate generated sucessfully"),
                ],
                max_length=10,
                null=True,
            ),
        ),
    ]