# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-17 05:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0016_userjoinrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='userjoinrequest',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]