# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-24 21:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0034_ia_edit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(blank=True, default='img/user_avatar/default.png', upload_to='img/user_avatar'),
        ),
    ]
