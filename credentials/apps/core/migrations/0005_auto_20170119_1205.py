from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_siteconfiguration_catalog_api_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteconfiguration',
            name='theme_scss_path',
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='certificate_help_url',
            field=models.URLField(help_text='URL of page for questions about certificates', null=True, verbose_name='Certificate Help URL'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='company_name',
            field=models.CharField(max_length=255, null=True, verbose_name='Company Name'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='homepage_url',
            field=models.URLField(null=True, verbose_name='Homepage URL'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='platform_name',
            field=models.CharField(help_text='Name of your Open edX platform', max_length=255, null=True, verbose_name='Platform Name'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='privacy_policy_url',
            field=models.URLField(null=True, verbose_name='Privacy Policy URL'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='tos_url',
            field=models.URLField(null=True, verbose_name='Terms of Service URL'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='verified_certificate_url',
            field=models.URLField(help_text='URL of page for information on verified certificates', null=True, verbose_name='Verified Certificate URL'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='lms_url_root',
            field=models.URLField(help_text="Root URL of this site's LMS (e.g. https://courses.stage.edx.org)", null=True, verbose_name='LMS base url for custom site'),
        ),
    ]
