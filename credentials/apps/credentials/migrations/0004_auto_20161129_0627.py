from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0003_programcertificate_use_org_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='programcertificate',
            name='program_uuid',
            field=models.UUIDField(unique=True, null=True, verbose_name='Program UUID', db_index=True),
        ),
        migrations.AlterField(
            model_name='programcertificate',
            name='program_id',
            field=models.PositiveIntegerField(help_text='This field is DEPRECATED. Use program_uuid instead.', unique=True, db_index=True),
        ),
    ]
