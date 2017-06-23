""" forms.py file for analysis app"""
from django import forms
from .models import datadrop,yeargroup

class importForm(forms.Form):
		username=forms.CharField(label="uname",max_length=50)
		pw=forms.CharField(label="pw",max_length=50,widget=forms.PasswordInput)
		cohort=forms.ModelChoiceField(label="year",queryset=yeargroup.objects.all())
		dd_name=forms.CharField(label="dd")
		dd_date=forms.DateField(label="dd_date",required=False)
	#class Meta:
		# dd_name=forms.CharField(label="dd",max_length=100)