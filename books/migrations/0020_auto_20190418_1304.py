# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-18 07:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0019_usermember_borrower'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registerentry',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='books.UserMember'),
        ),
    ]