# Generated by Django 2.2.24 on 2021-08-24 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_last_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='lms_user_id',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]
