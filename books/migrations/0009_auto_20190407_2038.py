# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-07 15:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0008_auto_20190406_2135'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='slug',
            field=models.SlugField(default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='book',
            name='acc',
            field=models.CharField(max_length=200, null=True),
        ),
    ]