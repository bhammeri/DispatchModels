# Generated by Django 2.2.5 on 2019-09-17 15:21

import dispatch.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dispatch', '0004_compressedjsonmodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compressedjsonmodel',
            name='value',
            field=dispatch.fields.CompressedJSONField(default=b''),
        ),
    ]
