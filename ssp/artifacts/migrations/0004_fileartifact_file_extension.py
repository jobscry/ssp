# Generated by Django 3.1.2 on 2020-10-09 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artifacts', '0003_auto_20201009_1702'),
    ]

    operations = [
        migrations.AddField(
            model_name='fileartifact',
            name='file_extension',
            field=models.CharField(default='unknown', max_length=25),
        ),
    ]