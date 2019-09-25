# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-09-15 06:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0005_publication_genre_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.IntegerField(default=0)),
                ('desc', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='genre',
            name='series',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='genres', to='books.Series'),
        ),
    ]
