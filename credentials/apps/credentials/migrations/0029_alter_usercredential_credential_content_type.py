# Generated by Django 4.2.13 on 2024-06-11 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("credentials", "0028_alter_historicalprogramcompletionemailconfiguration_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usercredential",
            name="credential_content_type",
            field=models.ForeignKey(
                limit_choices_to={"model__in": ("coursecertificate", "programcertificate", "credlybadgetemplate")},
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
        ),
    ]
