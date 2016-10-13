# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-13 13:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_usertoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='usertoken',
            name='expire_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
