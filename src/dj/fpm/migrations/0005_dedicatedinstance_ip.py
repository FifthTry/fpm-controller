# Generated by Django 3.2.13 on 2022-06-26 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fpm", "0004_auto_20220626_1331"),
    ]

    operations = [
        migrations.AddField(
            model_name="dedicatedinstance",
            name="ip",
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
