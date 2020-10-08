from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='signatory',
            name='organization_name_override',
            field=models.CharField(help_text='Signatory organization name if its different from issuing organization.', max_length=255, null=True, blank=True),
        ),
    ]
