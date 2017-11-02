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
	url(r'^interrogate/$',views.interrogate,name="interrogate"),
	url(r'^classes/(?P<cohort_string>\d{4}-\d{4})/(?P<subject_string>.*)$',views.subjAssessment,name='subjAssessment'),
	url(r'^interrogate/export$',views.interrogateExport,name="interrogateExport"),
	url(r'^view/(?P<focus>.*)/(?P<row_type>.*)/(?P<col_type>.*)$',views.stdTable_gen_getsession,name="stdTable_gen_getsession"),
	url(r'^view/(?P<focus>.*)/$',views.stdTable_gen,name="stdTable_gen"),

]
