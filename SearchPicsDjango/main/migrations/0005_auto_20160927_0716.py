# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-27 07:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_auto_20160906_1810'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='results',
            name='site',
        ),
        migrations.AddField(
            model_name='tasks',
            name='site',
            field=models.CharField(default='none', max_length=100),
            preserve_default=False,
        ),
    ]