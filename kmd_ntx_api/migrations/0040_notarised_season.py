# Generated by Django 2.2 on 2020-05-09 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmd_ntx_api', '0039_auto_20200509_0653'),
    ]

    operations = [
        migrations.AddField(
            model_name='notarised',
            name='season',
            field=models.CharField(default='unknown', max_length=32),
            preserve_default=False,
        ),
    ]