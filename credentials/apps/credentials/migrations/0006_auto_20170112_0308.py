from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0005_auto_20170111_0441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercredential',
            name='download_url',
            field=models.CharField(help_text='URL at which the credential can be downloaded', max_length=255, null=True, blank=True),
        ),
    ]
