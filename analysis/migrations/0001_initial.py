# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-02 15:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='classgroup',
            fields=[
                ('class_code', models.CharField(help_text="The class group's unique identifier code.", max_length=10, primary_key=True, serialize=False)),
                ('staff', models.CharField(help_text='The staff member(s) assigned to this group.', max_length=12)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='datadrop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The label identifying the \tdatadrop, e.g. Y9 DD3', max_length=30)),
                ('date', models.DateField(help_text='The date the datadrop ended.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='grade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress', models.IntegerField(blank=True, help_text='The progress the student has made from their baseline.', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='gradeMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(help_text='The identifying label for the grading scheme.', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='gradeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The grade symbol, e.g. A+, \t9=, 4.3, Pass', max_length=5)),
                ('progress_value', models.IntegerField(verbose_name="The value of the grade in the school's \tinternal progress system.")),
                ('att8_value', models.DecimalField(blank=True, decimal_places=1, help_text='The value of the grade towards Attainment 8.', max_digits=4)),
            ],
        ),
        migrations.CreateModel(
            name='headline',
            fields=[
                ('id', models.CharField(help_text='The datadrop and student \tupn the headline measures are linked to.', max_length=43, primary_key=True, serialize=False)),
                ('progress8', models.DecimalField(blank=True, decimal_places=2, help_text='The PROJECTED, INACCURATE Progress 8 figure calculated \t\t\tfor the student/DD.', max_digits=4, null=True)),
                ('attainment8', models.DecimalField(decimal_places=1, default=0, help_text='The Attainment8 calculated for the student/DD.', max_digits=3)),
                ('en_att8', models.DecimalField(decimal_places=1, default=0, help_text='The score for the English Att8 bucket.', max_digits=3)),
                ('ma_att8', models.DecimalField(decimal_places=1, default=0, help_text='The score for the Maths Att8 bucket.', max_digits=3)),
                ('eb_att8', models.DecimalField(decimal_places=1, default=0, help_text='The score for the EBacc Att8 bucket.', max_digits=3)),
                ('op_att8', models.DecimalField(decimal_places=1, default=0, help_text='The score for the Open Att8 bucket.', max_digits=3)),
                ('eb_filled', models.IntegerField(default=0, help_text='The number of subjects in the Ebacc Att8 bucket.')),
                ('op_filled', models.IntegerField(default=0, help_text='The number of subjects in the Open Att8 bucket.')),
                ('ebacc_entered', models.BooleanField(default=False, help_text='Whether the student qualified to enter the EBacc or not.')),
                ('ebacc_achieved_std', models.BooleanField(default=False, help_text='Whether the student achieved the EBacc (standard grade) or not.')),
                ('ebacc_achieved_stg', models.BooleanField(default=False, help_text='Whether the student achieved the EBacc (strong grade) or not.')),
                ('basics_9to4', models.BooleanField(default=False, help_text='Whether the student achieved a standard pass in both \t\tEnglish and Maths')),
                ('basics_9to5', models.BooleanField(default=False, help_text='Whether the student achieved a strong pass in both \t\tEnglish and Maths')),
                ('att8_progress', models.DecimalField(decimal_places=1, default=0, help_text='The difference in Attainment 8 score between this datadrop\t\t and baseline.', max_digits=3)),
                ('datadrop', models.ForeignKey(help_text='The datadrop the headline figures pertain to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.datadrop')),
            ],
        ),
        migrations.CreateModel(
            name='student',
            fields=[
                ('upn', models.CharField(help_text='Unique 13-character identifier used in many school systems.', max_length=13, primary_key=True, serialize=False)),
                ('forename', models.CharField(help_text="The student's forename(s).", max_length=50)),
                ('surname', models.CharField(help_text="The student's surname(s).", max_length=75)),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('N', 'Not Specified')], help_text='The gender identity of the student.', max_length=1)),
                ('ks2_reading', models.CharField(help_text="The student's reading score at the end of KS2.", max_length=5)),
                ('ks2_maths', models.CharField(help_text="The student's maths score at the end of KS2.", max_length=5)),
                ('ks2_average', models.CharField(help_text="The student's average reading and maths score at the end of\t\t\t KS2", max_length=5)),
                ('banding', models.CharField(choices=[('H', 'Upper/High Ability'), ('M', 'Middle Ability'), ('L', 'Lower Ability'), ('N', 'No data')], help_text='The ability\t\t grouping the student belongs to.', max_length=1)),
                ('eal', models.BooleanField(help_text='Whether the student has a native \t\tlanguage other than English.')),
                ('pp', models.BooleanField(help_text='Whether the student is a pupil premium \t\tstudent.')),
                ('sen', models.CharField(choices=[('N', 'Non SEN'), ('K', 'K SEN'), ('E', 'EHCP')], default='N', help_text='Special Educational Need code applicable to the student.', max_length=1)),
                ('lac', models.BooleanField(help_text='Whether the student is a Looked After \t\tChild (in social care).')),
                ('fsm_ever', models.BooleanField(help_text='Whether the student has ever been \t\teligible for Free School Meals.')),
            ],
        ),
        migrations.CreateModel(
            name='subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="The subject's name.", max_length=100)),
                ('attainment8bucket', models.CharField(choices=[('en', 'English'), ('ma', 'Maths'), ('eb', 'Ebacc'), ('op', 'Open')], help_text='The highest Attainment 8 bucket the subject can be counted in.', max_length=2)),
                ('faculty', models.CharField(blank=True, help_text='The faculty the subject is part of.', max_length=100, null=True)),
                ('option_subject', models.BooleanField(default=True)),
                ('ebacc_subject', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='yeargroup',
            fields=[
                ('cohort', models.CharField(choices=[('2017-2018', '2017-2018'), ('2018-2019', '2018-2019'), ('2019-2020', '2019-2020'), ('2020-2021', '2020-2021'), ('2021-2022', '2021-2022'), ('2022-2023', '2022-2023'), ('2023-2024', '2023-2024'), ('2024-2025', '2024-2025'), ('2025-2026', '2025-2026'), ('2026-2027', '2026-2027')], help_text='The graduating year of this yeargroup.', max_length=9, primary_key=True, serialize=False)),
                ('current_year', models.CharField(choices=[('7', 'Year 7'), ('8', 'Year 8'), ('9', 'Year 9'), ('10', 'Year 10'), ('11', 'Year 11')], help_text='The current yeargroup the cohort is in.', max_length=2)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='subject',
            name='cohort',
            field=models.ForeignKey(help_text='The yeargroup studying the subject.', on_delete=django.db.models.deletion.CASCADE, to='analysis.yeargroup'),
        ),
        migrations.AddField(
            model_name='subject',
            name='method',
            field=models.ForeignKey(help_text='The grade method used by the subject.', on_delete=django.db.models.deletion.CASCADE, to='analysis.gradeMethod'),
        ),
        migrations.AddField(
            model_name='student',
            name='cohort',
            field=models.ForeignKey(help_text='The yeargroup the student belongs to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.yeargroup'),
        ),
        migrations.AddField(
            model_name='student',
            name='reg',
            field=models.ForeignKey(help_text='The registration group the pupil belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='reg_group', to='analysis.classgroup'),
        ),
        migrations.AddField(
            model_name='headline',
            name='upn',
            field=models.ForeignKey(help_text='The student the headline figures pertain to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.student'),
        ),
        migrations.AddField(
            model_name='grademethod',
            name='pass_grade',
            field=models.ForeignKey(help_text='The grade considered a \t\tpass or strong pass for the purposes of headline measures (e.g. EnMa \t\tBasics, Ebacc).', on_delete=django.db.models.deletion.CASCADE, to='analysis.gradeValue'),
        ),
        migrations.AddField(
            model_name='grademethod',
            name='vals',
            field=models.ManyToManyField(help_text='The set of grades used/included in the grading method.', related_name='gradeset', to='analysis.gradeValue'),
        ),
        migrations.AddField(
            model_name='grade',
            name='EAPgrade',
            field=models.ForeignKey(blank=True, help_text='The estimated attainment for the student in this data drop.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='EAP', to='analysis.gradeValue'),
        ),
        migrations.AddField(
            model_name='grade',
            name='classgroup',
            field=models.ForeignKey(help_text='The class the grade was given in', null=True, on_delete=django.db.models.deletion.CASCADE, to='analysis.classgroup'),
        ),
        migrations.AddField(
            model_name='grade',
            name='datadrop',
            field=models.ForeignKey(help_text='The data drop that the grade is part of.', on_delete=django.db.models.deletion.CASCADE, to='analysis.datadrop'),
        ),
        migrations.AddField(
            model_name='grade',
            name='method',
            field=models.ForeignKey(help_text='The grade method the grade belongs to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.gradeMethod'),
        ),
        migrations.AddField(
            model_name='grade',
            name='subject',
            field=models.ForeignKey(help_text='The subject the grade was given in.', on_delete=django.db.models.deletion.CASCADE, to='analysis.subject'),
        ),
        migrations.AddField(
            model_name='grade',
            name='upn',
            field=models.ForeignKey(help_text='The UPN of the student the grade has been given to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.student'),
        ),
        migrations.AddField(
            model_name='grade',
            name='value',
            field=models.ForeignKey(help_text='The grade given.', on_delete=django.db.models.deletion.CASCADE, to='analysis.gradeValue'),
        ),
        migrations.AddField(
            model_name='datadrop',
            name='cohort',
            field=models.ForeignKey(help_text='The yeargroup the data drop belongs to.', on_delete=django.db.models.deletion.CASCADE, to='analysis.yeargroup'),
        ),
        migrations.AddField(
            model_name='classgroup',
            name='cohort',
            field=models.ForeignKey(help_text="The yeargroup that the class group's students belong to.", on_delete=django.db.models.deletion.CASCADE, to='analysis.yeargroup'),
        ),
        migrations.AddField(
            model_name='classgroup',
            name='subject',
            field=models.ManyToManyField(blank=True, help_text='The subject(s) studied by the group.', to='analysis.subject'),
        ),
    ]
