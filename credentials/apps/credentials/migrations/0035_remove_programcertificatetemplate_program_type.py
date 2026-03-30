from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0034_certificateasset_programcertificatetemplate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='programcertificatetemplate',
            name='program_type',
        ),
    ]
