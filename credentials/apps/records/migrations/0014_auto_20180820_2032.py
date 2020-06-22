# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-20 20:32


from django.db import migrations


def seed_user_credit_pathways(apps, schema_editor):
    UserCreditPathway = apps.get_model('records', 'UserCreditPathway')
    Pathway = apps.get_model('catalog', 'Pathway')
    for ucp in UserCreditPathway.objects.all():
        if not ucp.pathway and ucp.credit_pathway:
            site, uuid = ucp.credit_pathway.site, ucp.credit_pathway.uuid
            ucp.pathway = Pathway.objects.get(site=site, uuid=uuid)
            ucp.save()


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0013_usercreditpathway_pathway'),
    ]

    operations = [
        migrations.RunPython(seed_user_credit_pathways, migrations.RunPython.noop),
    ]
