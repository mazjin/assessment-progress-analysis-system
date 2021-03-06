# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-01-15 10:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_auto_20180112_1015'),
    ]

    operations = [
        migrations.CreateModel(
            name='subjectTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The string identifying the \ttag', max_length=100)),
            ],
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(help_text="The subject's name, as \ttimetabled.", max_length=100),
        ),
        migrations.AddField(
            model_name='subject',
            name='tags',
            field=models.ManyToManyField(help_text='Set of tags linking subject to other \tsubjects across yeargroups', to='analysis.subjectTag'),
        ),
    ]
