import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credentials', '0004_auto_20161129_0627'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercredential',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
