# Generated by Django 3.2.13 on 2022-07-03 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fpm", "0007_auto_20220703_0533"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="slug",
            field=models.SlugField(default="", unique=True),
            preserve_default=False,
        ),
    ]