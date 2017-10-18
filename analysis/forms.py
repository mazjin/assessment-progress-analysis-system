""" forms.py file for analysis app"""
from django import forms
from .models import datadrop,yeargroup,subject,classgroup
import json

class importForm(forms.Form):
	"""takes input to start process of importation from SISRA"""
	username=forms.CharField(label="SISRA username",max_length=50)
	pw=forms.CharField(label="Password",
		max_length=50,widget=forms.PasswordInput)
	cohort=forms.ModelChoiceField(label="Cohort",
		queryset=yeargroup.objects.all())
	dd_name=forms.CharField(label="Datadrop")
	dd_date=forms.DateField(label="Date of Datadrop",required=False)

class interrogatorForm(forms.Form):
	"""takes input to dictate query for interrogator table"""
	GROUPINGS=(#possible row or column queries
		('student','Student Attributes'),
		('extended_student','Full Student Attributes'),
		('yeargroup','Yeargroups'),
		('datadrop','Data Drops'),
		('classgroup','Class groups'),
		('banding','Ability Bands'),
		('subject','Subjects'),
		('faculty','Faculties'),
		('att8bucket','Attainment 8 Bucket'),
		('subject_blocks','Subject Blocks'),
		)

	VALUES=(#possible cell value queries
		('progress','Progress Score'),
		('meeting','Meeting/Exceeding EAP'),
		('exceeding','Exceeding EAP'),
		('attainment8','Attainment 8'),
		('progress8','Progress 8'),
		('att8_progress','Δ Attainment 8'),
		('ppGap','Pupil Premium Gap'),
		('en_att8','English Att8 Bucket'),
		('ma_att8','Maths Att8 Bucket'),
		('eb_att8','EBacc Att8 Bucket'),
		('op_att8','Open Att8 Bucket'),
		('eb_filled','Subjects in EBacc Bucket'),
		('op_filled','Subjects in Open Bucket'),
		('ebacc_entered','Entered for EBacc'),
		('ebacc_achieved_std','Achieving EBacc (4+)'),
		('ebacc_achieved_stg','Achieving EBacc (5+)'),
		('basics_9to4','Basics 4+'),
		('basics_9to5','Basics 5+'),
		)


	row_choice=forms.ChoiceField(label="Row Grouping",
		choices=GROUPINGS,required=True)

	col_choice=forms.ChoiceField(label="Column Grouping",
		choices=GROUPINGS,required=True)

	val_choice=forms.ChoiceField(label="Cell Value Type",
		choices=VALUES,required=True)

	#returns table values as a residual from the "All" column/row
	residual_toggle_col=forms.BooleanField(label="Calculate residual by col",
		required=False)
	residual_toggle_row=forms.BooleanField(label="Calculate residual by row",
		required=False)

	"""below options limit query to specific objects/groups"""
	yeargroup_selected=forms.ModelChoiceField(label="Cohort",
		queryset=yeargroup.objects.all(),required=False)
	subject_selected=forms.ModelChoiceField(label="Subject",
		queryset=subject.objects.all(),required=False)
	classgroup_selected=forms.ModelChoiceField(label="Class/Form group",
		queryset=classgroup.objects.all(), required=False)
	datadrop_selected=forms.ModelChoiceField(label="Datadrop",
		queryset=datadrop.objects.all(),required=False)

	"""when filtering for a specific subject/data drop, decides whether to match
	grades with the same name instead of the same specific object - allows
	matching subjects/data drops of across yeargroups"""
	match_subject_by_name=forms.BooleanField(label="Match Subject across \
		yeargroups",required=False)
	match_datadrop_by_name=forms.BooleanField(label="Match Datadrop across \
		yeargroups",required=False)

class standardTableForm_subject(forms.Form):
	dsubs={}
	list_subs=[]
	for sub in subject.objects.all().order_by('name'):
		if sub.cohort.__str__() in dsubs:
			dsubs[sub.cohort.__str__()].append(sub.name)
		else:
			dsubs[sub.cohort.__str__()]=[sub.name]
		list_subs.append((sub.name, sub.name))

	years=[year.__str__() for year in yeargroup.objects.all()]
	list_subs=sorted(list(set(list_subs)))
	yeargroup_selected= forms.ChoiceField(choices=([(year,year) for year in years]))
	subject_selected=forms.ChoiceField(choices=(list_subs))

	years=json.dumps(years)
	subs=json.dumps(dsubs)


	# subject_selected=forms.ModelChoiceField(label="Subject",queryset=subject.objects.all(),required=True)
	# yeargroup_selected=forms.ModelChoiceField(label="Cohort",
		# queryset=yeargroup.objects.all(),required=False)

class standardTableForm_classgroup(forms.Form):
	dsubs={}
	list_subs=[]
	for sub in subject.objects.all().order_by('name'):
		if sub.cohort.__str__() in dsubs:
			dsubs[sub.cohort.__str__()].append(sub.name)
		else:
			dsubs[sub.cohort.__str__()]=[sub.name]
		list_subs.append((sub.name,sub.name))

	dclasses={}
	list_classes=[]
	for clsgp in classgroup.objects.all().order_by('class_code').exclude(subject=None):
		for sub in clsgp.subject.all():
			if (clsgp.cohort.__str__()+","+sub.name) in dclasses:
				dclasses[clsgp.cohort.__str__()+","+sub.name].append(clsgp.class_code)
			else:
				dclasses[clsgp.cohort.__str__()+","+sub.name]=[clsgp.class_code]
		list_classes.append((clsgp.class_code,clsgp.class_code))

	years=[year.__str__() for year in yeargroup.objects.all()]

	yeargroup_selected=forms.ChoiceField(choices=([(year,year) for year in years]))
	subject_selected=forms.ChoiceField(choices=(list_subs))
	classgroup_selected=forms.ChoiceField(choices=(list_classes))

	years=json.dumps(years)
	subs=json.dumps(dsubs)
	classes=json.dumps(dclasses)

class standardTableForm_datadrop(forms.Form):
	years=[year.__str__() for year in yeargroup.objects.all()]
	ddrops={}
	list_drops=[]
	for drop in datadrop.objects.all().order_by('name'):
		if drop.cohort.__str__() in ddrops:
			ddrops[drop.cohort.__str__()].append(drop.name)
		else:
			ddrops[drop.cohort.__str__()]=[drop.name]
		list_drops.append((drop.name,drop.name))

	dsubs={}
	list_subs=[]
	for sub in subject.objects.all().order_by('name'):
		if sub.cohort.__str__() in dsubs:
			dsubs[sub.cohort.__str__()].append(sub.name)
		else:
			dsubs[sub.cohort.__str__()]=[sub.name]
		list_subs.append((sub.name,sub.name))

	dclasses={}
	list_classes=[]
	for clsgp in classgroup.objects.all().order_by('class_code').exclude(subject=None):
		for sub in clsgp.subject.all():
			if (clsgp.cohort.__str__()+","+sub.name) in dclasses:
				dclasses[clsgp.cohort.__str__()+","+sub.name].append(clsgp.class_code)
			else:
				dclasses[clsgp.cohort.__str__()+","+sub.name]=[clsgp.class_code]
		list_classes.append((clsgp.class_code,clsgp.class_code))
	yeargroup_selected=forms.ChoiceField(choices=([(year,year) for year in years]))
	datadrop_selected=forms.ChoiceField(choices=(list_drops))
	subject_selected=forms.ChoiceField(choices=(list_subs),required=False)
	classgroup_selected=forms.ChoiceField(choices=(list_classes),required=False)
