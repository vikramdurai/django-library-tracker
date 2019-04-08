# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-08 09:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0012_auto_20190408_1013'),
    ]

    operations = [
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='publication',
            name='copies',
        ),
        migrations.RemoveField(
            model_name='publication',
            name='date_added',
        ),
        migrations.AddField(
            model_name='book',
            name='date_added',
            field=models.DateTimeField(null=True, verbose_name='Date added to the library'),
        ),
        migrations.AddField(
            model_name='extendlog',
            name='entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='books.RegisterEntry'),
        ),
        migrations.AddField(
            model_name='book',
            name='library',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='books.Library'),
        ),
        migrations.AddField(
            model_name='registerentry',
            name='library',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='books.Library'),
        ),
        migrations.AddField(
            model_name='userstaff',
            name='library',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='books.Library'),
        ),
    ]
