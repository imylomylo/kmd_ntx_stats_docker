# Generated by Django 2.2 on 2020-05-08 14:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmd_ntx_api', '0033_mined_season'),
    ]

    operations = [
        migrations.AddField(
            model_name='mined',
            name='block_datetime',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 8, 14, 45, 28, 5970)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notarised',
            name='block_datetime',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 8, 14, 45, 49, 787934)),
            preserve_default=False,
        ),
    ]
