""" forms.py file for analysis app"""
from django import forms
from .models import datadrop,yeargroup,subject,classgroup

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
		# add other headlines to this, eg. att8 by bucket, basics,ebacc
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