from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160331_0218'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='catalog_api_url',
            field=models.URLField(help_text='Root URL of the Catalog API (e.g. https://api.edx.org/catalog/v1/)', null=True, verbose_name='Catalog API URL'),
        ),
    ]
