# Generated by Django 2.2.16 on 2020-10-21 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0013_drop_old_start_end_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='type_slug',
            field=models.CharField(default='', max_length=32),
        ),
    ]
