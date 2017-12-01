# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-25 23:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_battlehistory_max_step'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='battlehistory',
            name='status',
        ),
        migrations.AddField(
            model_name='battlehistory',
            name='is_finished',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
