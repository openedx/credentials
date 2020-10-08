from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0006_auto_20170112_0308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programcertificate',
            name='program_id',
            field=models.PositiveIntegerField(help_text='This field is DEPRECATED. Use program_uuid instead.', unique=True, null=True, db_index=True, blank=True),
        ),
    ]
