# Generated by Django 2.2.5 on 2019-09-23 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dispatch', '0009_csvfileupload'),
    ]

    operations = [
        migrations.AlterField(
            model_name='csvfileupload',
            name='upload_date',
            field=models.DateTimeField(auto_created=True, auto_now_add=True),
        ),
    ]
