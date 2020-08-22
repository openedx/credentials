# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-04-11 15:23


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_auto_20170410_1646"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siteconfiguration",
            name="verified_certificate_url",
            field=models.URLField(
                blank=True,
                help_text="This field is deprecated, and will be removed.",
                null=True,
                verbose_name="Verified Certificate URL",
            ),
        ),
    ]
