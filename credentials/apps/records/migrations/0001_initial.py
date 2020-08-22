# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-06-01 14:27


import django.db.models.deletion
import django_extensions.db.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserGrade",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("letter_grade", models.CharField(max_length=255)),
                ("percent_grade", models.DecimalField(decimal_places=4, max_digits=5)),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("honor", "honor"),
                            ("professional", "professional"),
                            ("verified", "verified"),
                        ],
                        max_length=255,
                    ),
                ),
                (
                    "course_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalog.CourseRun",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="usergrade", unique_together=set([("user", "course_run")]),
        ),
    ]
