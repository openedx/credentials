import uuid

import django_extensions.db.fields
from django.db import migrations, models

import credentials.apps.credentials.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(unique=True, max_length=255, db_index=True)),
                ('content', models.TextField(help_text='HTML Template content data.')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
        ),
        migrations.CreateModel(
            name='CertificateTemplateAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
        ),
        migrations.CreateModel(
            name='CourseCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('is_active', models.BooleanField(default=False)),
                ('title', models.CharField(help_text='Custom certificate title to override default display_name for a course/program.', max_length=255, null=True, blank=True)),
                ('course_id', models.CharField(max_length=255, validators=[credentials.apps.credentials.models.validate_course_key])),
                ('certificate_type', models.CharField(max_length=255, choices=[('honor', 'honor'), ('professional', 'professional'), ('verified', 'verified')])),
            ],
            options={
                'verbose_name': 'Course certificate configuration',
            },
        ),
        migrations.CreateModel(
            name='ProgramCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('is_active', models.BooleanField(default=False)),
                ('title', models.CharField(help_text='Custom certificate title to override default display_name for a course/program.', max_length=255, null=True, blank=True)),
                ('program_id', models.PositiveIntegerField(unique=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Program certificate configuration',
            },
        ),
        migrations.CreateModel(
            name='Signatory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('image', models.ImageField(help_text='Image must be square PNG files. The file size should be under 250KB.', upload_to=credentials.apps.credentials.models.signatory_assets_path, validators=[credentials.apps.credentials.models.validate_image])),
            ],
            options={
                'verbose_name_plural': 'Signatories',
            },
        ),
        migrations.CreateModel(
            name='UserCredential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('credential_id', models.PositiveIntegerField()),
                ('username', models.CharField(max_length=255, db_index=True)),
                ('status', models.CharField(default='awarded', max_length=255, choices=[('awarded', 'awarded'), ('revoked', 'revoked')])),
                ('download_url', models.CharField(help_text='Download URL for the PDFs.', max_length=255, null=True, blank=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('credential_content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='UserCredentialAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('user_credential', models.ForeignKey(related_name='attributes', to='credentials.UserCredential', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='programcertificate',
            name='signatories',
            field=models.ManyToManyField(to='credentials.Signatory'),
        ),
        migrations.AddField(
            model_name='programcertificate',
            name='site',
            field=models.ForeignKey(to='sites.Site', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='programcertificate',
            name='template',
            field=models.ForeignKey(blank=True, to='credentials.CertificateTemplate', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='coursecertificate',
            name='signatories',
            field=models.ManyToManyField(to='credentials.Signatory'),
        ),
        migrations.AddField(
            model_name='coursecertificate',
            name='site',
            field=models.ForeignKey(to='sites.Site', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='coursecertificate',
            name='template',
            field=models.ForeignKey(blank=True, to='credentials.CertificateTemplate', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='usercredentialattribute',
            unique_together={('user_credential', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='usercredential',
            unique_together={('username', 'credential_content_type', 'credential_id')},
        ),
        migrations.AlterUniqueTogether(
            name='coursecertificate',
            unique_together={('course_id', 'certificate_type', 'site')},
        ),
    ]
