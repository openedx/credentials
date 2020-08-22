# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-22 16:55


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("records", "0015_auto_20180821_1636"),
    ]

    operations = [
        migrations.RemoveField(model_name="usercreditpathway", name="credit_pathway",),
        migrations.AlterField(
            model_name="usercreditpathway",
            name="pathway",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="catalog.Pathway"
            ),
        ),
    ]
