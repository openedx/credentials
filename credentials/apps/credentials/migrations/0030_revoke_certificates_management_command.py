# Generated by Django 4.2.16 on 2024-12-04 20:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("credentials", "0029_alter_usercredential_credential_content_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="RevokeCertificatesConfig",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("change_date", models.DateTimeField(auto_now_add=True, verbose_name="Change date")),
                ("enabled", models.BooleanField(default=False, verbose_name="Enabled")),
                (
                    "arguments",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text='Arguments for a management command, eg. "--certificate_id 222 --lms_user_ids 867 5309 925".',
                    ),
                ),
                (
                    "changed_by",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Changed by",
                    ),
                ),
            ],
            options={
                "verbose_name": "revoke_certificates argument",
            },
        ),
    ]
