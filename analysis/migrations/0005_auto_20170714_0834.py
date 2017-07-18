# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-14 07:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_auto_20170629_1205'),
    ]

    operations = [
        migrations.CreateModel(
            name='headline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress8', models.DecimalField(blank=True, decimal_places=2, help_text='The PROJECTED, INACCURATE Progress 8 figure calculated \t\t\tfor the student/DD.', max_digits=4, null=True)),
                ('attainment8', models.IntegerField(default=0, help_text='The Attainment8 calculated for the student/DD.')),
                ('en_att8', models.IntegerField(default=0, help_text='The score for the English Att8 bucket.')),
                ('ma_att8', models.IntegerField(default=0, help_text='The score for the Maths Att8 bucket.')),
                ('eb_att8', models.IntegerField(default=0, help_text='The score for the EBacc Att8 bucket.')),
                ('op_att8', models.IntegerField(default=0, help_text='The score for the Open Att8 bucket.')),
                ('eb_filled', models.IntegerField(default=0, help_text='The number of subjects in the Ebacc Att8 bucket.')),
                ('op_filled', models.IntegerField(default=0, help_text='The number of subjects in the Open Att8 bucket.')),
                ('ebacc_entered', models.BooleanField(default=False, help_text='Whether the student qualified to enter the EBacc or not.')),
                ('ebacc_achieved', models.BooleanField(default=False, help_text='Whether the student achieved the EBacc or not.')),
                ('basics_9to4', models.BooleanField(default=False, help_text='Whether the student achieved a standard pass in both \t\tEnglish and Maths')),
                ('basics_9to5', models.BooleanField(default=False, help_text='Whether the student achieved a strong pass in both \t\tEnglish and Maths')),
                ('att8_progress', models.IntegerField(default=0, help_text='The difference in Attainment 8 score between this datadrop\t\t and baseline.')),
            ],
        ),
        migrations.AlterField(
            model_name='classgroup',
            name='class_code',
            field=models.CharField(help_text="The class group's unique identifier code.", max_length=10, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='datadrop',
            name='name',
            field=models.CharField(help_text='The label identifying the \tdatadrop, e.g. Y9 DD3', max_length=30),
        ),
        migrations.AlterField(
            model_name='grademethod',
            name='pass_grade',
            field=models.ForeignKey(help_text='The grade considered a \t\tpass or strong pass for the purposes of headline measures (e.g. EnMa \t\tBasics, Ebacc).', on_delete=django.db.models.deletion.CASCADE, to='analysis.gradeValue'),
        ),
        migrations.AlterField(
            model_name='gradevalue',
            name='name',
            field=models.CharField(help_text='The grade symbol, e.g. A+, \t9=, 4.3, Pass', max_length=5),
        ),
        migrations.AlterField(
            model_name='gradevalue',
            name='progress_value',
            field=models.IntegerField(verbose_name="The value of the grade in the school's \tinternal progress system."),
        ),
        migrations.AlterField(
            model_name='student',
            name='banding',
            field=models.CharField(choices=[('H', 'Upper/High Ability'), ('M', 'Middle Ability'), ('L', 'Lower Ability'), ('N', 'No data')], help_text='The ability\t\t grouping the student belongs to.', max_length=1),
        ),
        migrations.AlterField(
            model_name='student',
            name='eal',
            field=models.BooleanField(help_text='Whether the student has a native \t\tlanguage other than English.'),
        ),
        migrations.AlterField(
            model_name='student',
            name='fsm_ever',
            field=models.BooleanField(help_text='Whether the student has ever been \t\teligible for Free School Meals.'),
        ),
        migrations.AlterField(
            model_name='student',
            name='ks2_average',
            field=models.CharField(help_text="The student's average reading and maths score at the end of\t\t\t KS2", max_length=5),
        ),
        migrations.AlterField(
            model_name='student',
            name='lac',
            field=models.BooleanField(help_text='Whether the student is a Looked After \t\tChild (in social care).'),
        ),
        migrations.AlterField(
            model_name='student',
            name='pp',
            field=models.BooleanField(help_text='Whether the student is a pupil premium \t\tstudent.'),
        ),
        migrations.AlterField(
            model_name='student',
            name='sen',
            field=models.CharField(choices=[('N', 'Non SEN'), ('K', 'K SEN'), ('E', 'EHCP')], default='N', help_text='Special Educational Need code applicable to the student.', max_length=1),
        ),
        migrations.AddField(
            model_name='headline',
            name='datadrop',
            field=models.ForeignKey(help_text='The datadrop the headline figures pertain to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.datadrop'),
        ),
        migrations.AddField(
            model_name='headline',
            name='upn',
            field=models.ForeignKey(help_text='The student the headline figures pertain to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.student'),
        ),
    ]