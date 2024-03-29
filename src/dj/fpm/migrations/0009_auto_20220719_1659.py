# Generated by Django 3.2.13 on 2022-07-19 11:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("fpm", "0008_package_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="domain_state",
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
        migrations.AddField(
            model_name="package",
            name="site",
            field=models.OneToOneField(
                default=1, on_delete=django.db.models.deletion.PROTECT, to="sites.site"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="packagedomainmap",
            name="package",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="domains",
                to="fpm.package",
            ),
        ),
    ]
