from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0002_signatory_organization_name_override'),
    ]

    operations = [
        migrations.AddField(
            model_name='programcertificate',
            name='use_org_name',
            field=models.BooleanField(default=False, help_text="Display the associated organization's name (e.g. ACME University) instead of its short name (e.g. ACMEx)", verbose_name='Use organization name'),
        ),
    ]
