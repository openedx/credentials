# Generated by Django 1.11.11 on 2018-07-17 20:02


from django.db import migrations

from credentials.apps.catalog.models import Program
from credentials.apps.records.models import ProgramCertRecord


def seed_program_cert_records(apps, schema_editor):
    for pcr in ProgramCertRecord.objects.all():
        if pcr.certificate is None:
            continue
        program_uuid = pcr.certificate.program_uuid
        site = pcr.certificate.site
        pcr.program = Program.objects.get(site=site, uuid=program_uuid)
        pcr.save()


class Migration(migrations.Migration):

    dependencies = [
        ("records", "0005_auto_20180717_1953"),
    ]

    operations = [
        migrations.RunPython(seed_program_cert_records),
    ]
