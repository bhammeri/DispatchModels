# Generated by Django 2.2.5 on 2019-09-17 15:23

import dispatch.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dispatch', '0005_auto_20190917_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeseries',
            name='data',
            field=dispatch.fields.CompressedJSONField(default=b''),
        ),
    ]
