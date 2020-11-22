# Generated by Django 3.1.2 on 2020-10-21 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0008_detail_file_artifacts'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fileartifact',
            options={'ordering': ('name',)},
        ),
        migrations.AlterField(
            model_name='detail',
            name='file_artifacts',
            field=models.ManyToManyField(blank=True, to='plans.FileArtifact'),
        ),
    ]
