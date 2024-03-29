# Generated by Django 2.2.5 on 2019-09-23 08:38

import dispatch.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dispatch', '0008_thermalplantdispatch_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='CSVFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_date', models.DateTimeField(auto_created=True)),
                ('file', models.FileField(upload_to=dispatch.models.unique_filename_user_directory, validators=[dispatch.models.csv_validator])),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
