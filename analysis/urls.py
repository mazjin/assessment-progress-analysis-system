"""Defines URL patterns for analysis app"""

from django.conf.urls import url

from . import views

urlpatterns=[
	#Homepage
	url(r'^$',views.index,name="index"),
	#url(r'^interrogate/$',views.interrogate,name="interrogate"),
	url(r'^cohorts/$',views.yeargroups,name="yeargroups"),
	url(r'^classes/(?P<cohort_string>\d{4}-\d{4})$',views.yeargroupClasses,name='yeargroupClasses'),
	url(r'^subjects/(?P<cohort_string>\d{4}-\d{4})$',views.yeargroupSubjects,name='yeargroupSubjects'),
	url(r'^import/$',views.importPrompt,name="importPrompt"),
	#url(r'^quickquery/$',views.quickDisplayDF, name="quickDisplayDF"),
	url(r'^classes/(?P<cohort_string>\d{4}-\d{4})/(?P<subject_string>.*)$',views.subjAssessment,name='subjAssessment'),
]