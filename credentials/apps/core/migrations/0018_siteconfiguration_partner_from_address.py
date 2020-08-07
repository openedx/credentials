# Generated by Django 1.11.11 on 2018-07-11 13:41


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20180619_1859'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='partner_from_address',
            field=models.EmailField(blank=True,
                                    help_text='An address to use for the "From" field of any automated emails sent out to partners. If not defined, no-reply@sitedomain will be used.',
                                    max_length=254, null=True, verbose_name='Email address for partners'),
        ),
    ]
