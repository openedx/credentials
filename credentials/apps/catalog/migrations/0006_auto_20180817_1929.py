# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-17 19:29


from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("catalog", "0005_auto_20180816_1815"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pathway",
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
                ("uuid", models.UUIDField(verbose_name="UUID")),
                ("name", models.CharField(max_length=255)),
                ("org_name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                (
                    "programs",
                    sortedm2m.fields.SortedManyToManyField(
                        help_text=None, to="catalog.Program"
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sites.Site"
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="pathway", unique_together=set([("site", "uuid")]),
        ),
    ]
