""" forms.py file for analysis app"""
from django import forms
from .models import datadrop,yeargroup,subject,classgroup

class importForm(forms.Form):
	"""takes input to start process of importation from SISRA"""
	username=forms.CharField(label="uname",max_length=50)
	pw=forms.CharField(label="pw",
		max_length=50,widget=forms.PasswordInput)
	cohort=forms.ModelChoiceField(label="year",
		queryset=yeargroup.objects.all())
	dd_name=forms.CharField(label="dd")
	dd_date=forms.DateField(label="dd_date",required=False)

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
		('att8','Attainment 8'),
		#('p8','Progress 8'),
		('ppGap','Pupil Premium Gap'),
		)
	

	row_choice=forms.ChoiceField(label="rowChoice",
		choices=GROUPINGS,required=True)
		
	col_choice=forms.ChoiceField(label="colChoice",
		choices=GROUPINGS,required=True)
		
	val_choice=forms.ChoiceField(label="valChoice",
		choices=VALUES,required=True)
	
	#returns table values as a residual from the "All" column/row
	residual_toggle_col=forms.BooleanField(label="residualToggleCol",
		required=False)
	residual_toggle_row=forms.BooleanField(label="residualToggleRow",
		required=False)
	
	"""below options limit query to specific objects/groups"""
	yeargroup_selected=forms.ModelChoiceField(label="cohort",
		queryset=yeargroup.objects.all(),required=False)
	subject_selected=forms.ModelChoiceField(label="subject",
		queryset=subject.objects.all(),required=False)
	classgroup_selected=forms.ModelChoiceField(label="classgroup",
		queryset=classgroup.objects.all(), required=False)
	datadrop_selected=forms.ModelChoiceField(label="datadrop",
		queryset=datadrop.objects.all(),required=False)
	
	"""when filtering for a specific subject/data drop, decides whether to match
	grades with the same name instead of the same specific object - allows
	matching subjects/data drops of across yeargroups"""
	match_subject_by_name=forms.BooleanField(label="Match Subject across \
		yeargroups",required=False)
	match_datadrop_by_name=forms.BooleanField(label="Match Datadrop across \
		yeargroups",required=False)