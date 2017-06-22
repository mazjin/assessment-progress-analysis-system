# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-07 09:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_interrogator', '0003_auto_20160307_1444'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datatable',
            name='base_model',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='datatablepage',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='draft', help_text='Draft items will only be seen by super users, published items can be seen by those allowed by the registration required field.', max_length=20),
        ),
        migrations.AlterField(
            model_name='datatablepagecolumn',
            name='column_definition',
            field=models.TextField(help_text='The definition used to extract data from the database'),
        ),
        migrations.AlterField(
            model_name='datatablepagecolumn',
            name='header_text',
            field=models.CharField(blank=True, help_text='The text displayed in the table header for this column', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='datatablepagecolumn',
            name='position',
            field=models.PositiveSmallIntegerField(verbose_name='Position'),
        ),
        migrations.AlterField(
            model_name='datatablepagefilter',
            name='filter_definition',
            field=models.TextField(help_text='The definition used to extract data from the database'),
        ),
    ]
