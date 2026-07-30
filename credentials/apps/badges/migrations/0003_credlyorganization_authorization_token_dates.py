from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('badges', '0002_accredibleapiconfig_accrediblebadge_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='credlyorganization',
            name='authorization_token_created_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the current Credly authorization token was first issued.',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='credlyorganization',
            name='authorization_token_updated_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the current Credly authorization token was last refreshed (rotated).',
                null=True,
            ),
        ),
    ]
