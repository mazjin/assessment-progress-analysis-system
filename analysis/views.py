from django.shortcuts import render
from .models import *
from .sisraTools import *
from selenium import webdriver
from django.http import HttpResponseRedirect,HttpResponse
from assessment import settings
import sqlite3
import time
import pandas as pd
import numpy as np
from .colourCodingRules import colour_progress,colour_pp_gap,colour_pp_gap_df,\
	colour_progress_df,colour_mx_EAP
import seaborn as sns
import io
from django.apps import apps
import pickle
import os

# Create your views here.

def index(request):
	"""renders home page for assessment tools"""
	return render(request, 'analysis/index.html')

def faq(request):
	"""renders faq page"""
	return render(request,'analysis/faq.html')

def yeargroups(request):
	"""renders a page that lists all cohorts with available data."""
	yeargroups=yeargroup.objects.all()
	context={'yeargroups':yeargroups}
	return render(request, 'analysis/yeargroups.html',context)

def yeargroupClasses(request,cohort_string):
	"""lists all classgroups for a cohort"""
	selected_yeargroup=yeargroup.objects.get(cohort=cohort_string)
	classes=selected_yeargroup.classgroup_set.order_by('subject','class_code')
	context={'cohort':selected_yeargroup,'classes':classes}
	return render(request,'analysis/yeargroupByClasses.html',context)

def yeargroupSubjects(request,cohort_string):
	"""lists all classgroups for a cohort"""
	selected_yeargroup=yeargroup.objects.get(cohort=cohort_string)
	subjects=selected_yeargroup.subject_set.order_by('name')
	context={'cohort':selected_yeargroup,'subjects':subjects}
	return render(request,'analysis/yeargroupBySubjects.html',context)

def subjAssessment(request,cohort_string,subject_string):
	"""lists all classgroups for a cohort"""
	selected_subject=subject.objects.get(name=subject_string,cohort=yeargroup.\
		objects.get(cohort=cohort_string))
	classes=selected_subject.classgroup_set.order_by('subject','class_code')
	context={'subject':selected_subject,'classes':classes}
	return render(request,'analysis/subjAssessment.html',context)

def get_subject_type_info(subj_name):
	"""returns set of values that define groupings for subjects based on name
	for importation"""
	ebacc_bool=False
	option_bool=True
	faculty=None
	bkt="op"
	if "English" in subj_name:
		bkt="en"
		ebacc_bool=True
		option_bool=False
		faculty="English"
	elif "Math" in subj_name:
		bkt="ma"
		ebacc_bool=True
		option_bool=False
		faculty="Maths"
	elif "Science" in subj_name:
		bkt="eb"
		ebacc_bool=True
		if subj_name=="Computer Science":
			faculty="IT"
		else:
			option_bool=False
			faculty="Science"
	elif subj_name in ["History","Geography"]:
		bkt="eb"
		ebacc_bool=True
		faculty="Humanities"
	elif subj_name in ["Spanish","French","MFL"]:
		bkt="eb"
		ebacc_bool=True
		faculty="MFL"
	elif "Business" in subj_name or "ICT" in subj_name:
		faculty="IT"
	elif "Food" in subj_name or "Materials" in subj_name:
		faculty="Technology"
	elif subj_name in ["Art","Drama","Music","Media Studies"]:
		faculty="Arts"
	return ebacc_bool,option_bool,faculty,bkt

def importPrompt(request):
	from .forms import importForm
	"""for none-POST requests, renders input form to start importation, for
	POST requests, imports data from SISRA using entered values"""
	if request.method !="POST":
		form=importForm()
	else:
		form=importForm(data=request.POST)
		if form.is_valid():
			username=form.cleaned_data.get('username')
			pw=form.cleaned_data.get('pw')
			cohort=form.cleaned_data.get('cohort').current_year
			dd_name=form.cleaned_data.get('dd_name').strip().upper()
			dd_obj,dd_created=datadrop.objects.get_or_create(name=dd_name,
				cohort=form.cleaned_data.get('cohort'),defaults={
					'date':form.cleaned_data.get('dd_date')})
			if dd_created:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
					"New data drop " + dd_name + " created for Year "+cohort+\
					". Getting ready to import data...")
			else:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
					"Data drop " + dd_name + " located for Year "+cohort+\
					". Getting ready to update data...")
			try:
				print('Checking for unfinished imports...')
				with open("lastUnfinishedImportCuY" + cohort + dd_name +".p","rb") as fp:
					impDict=pickle.load(fp)
					students_df=impDict['students']
					grades_df=impDict['grades']
					headlines_df=impDict['headlines']
				print('Found! Continuing last unfinished import...')
			except:
				print('No unfinished imports found, importing from SISRA...')
				#open browser for SISRA access
				browser=webdriver.Chrome()
				"""use routines from sisraTools module to navigate to and retrieve
				student data"""
				logIntoSISRA(username,pw,browser)
				openStudentReports(browser,cohort,dd_name)
				students_df,grades_df,headlines_df=getStudentData(browser,cohort,dd_name)
				impDict={'students':students_df,'grades':grades_df,'headlines':headlines_df}
				with open("lastUnfinishedImportCuY" + cohort + dd_name +".p","wb") as fp:
					pickle.dump(impDict,fp)
				#close browser
				browser.close()
			students_df['cohort']=form.cleaned_data.get('cohort')
			print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
				"Student records retrieved, importing...")
			#instantiate lists for feedback output
			failed_upns=[]
			failed_grades=[]
			created_classes=[]
			created_subjects=[]
			multiple_classes=[]
			failed_headlines=[]
			#variables to track progress through importation processing
			student_position=1
			student_number=len(students_df.index)
			student_milestone=int(student_number/15)
			if student_milestone<2:
				student_milestone=1
			"""loop through rows in returned student dataframe, format and
			add to db"""
			for u,stu in students_df.iterrows():
				if student_position % student_milestone==1:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
						"Importing " + str(student_position) + " of " + \
						str(student_number) + " students...")
				try:
					#formatting banding
					if stu['banding']=="Lower":
						band="L"
					elif stu['banding']=="Upper/High":
						band="H"
					elif stu['banding']=="Middle":
						band="M"
					else:
						band="N"
					#determining appropriate reg group
					reggroup,reg_created=classgroup.objects.get_or_create(
						class_code="CLS"+stu['reg'].strip(),defaults={
						'cohort':form.cleaned_data.get('cohort'),'staff':"---"})
					#constructing student object & saving to db
					created_student=student(upn=u,forename=stu['forename'],
						surname=stu['surname'],
						reg=reggroup,
						gender=stu['gender'][0].upper(),
						cohort=stu['cohort'],
						ks2_reading=stu['ks2_reading'],
						ks2_maths=stu['ks2_maths'],
						ks2_average=stu['ks2_average'],
						banding=band,
						eal=stu['eal']=="Yes",
						pp=stu['pp']=="Yes",
						sen=stu['sen'][0],
						lac=stu['lac']=="Yes",
						fsm_ever=stu['fsm_ever']=="Yes")
					created_student.save()

					if reg_created:#add to output
						created_classes.append(created_student.reg.class_code)
					student_position+=1
				except:#add to output
					failed_upns.append(u)

			#instantiate formatted grades dataframe
			new_grades_df=pd.DataFrame(columns=['upn','Qualification Name',
				'Basket','Class','Type','Grade','Att8 Points','EAP Grade',
				'staff','Compare Grade','progress','method','subject',
				'classgroup','datadrop','value','EAPgrade','baseline_grade'])

			#variables to track progress though grades importation routine
			ii=0 #counter for valid grades
			grade_number=len(grades_df.index)
			grade_milestone=int(grade_number/15)
			if grade_milestone<2:
				grade_milestone=1
			"""loop through retrieved grades dataframe by row, format and put
			into new dataframe"""
			for i, gr in grades_df.iterrows():
				if ii % grade_milestone==0:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
						"Importing grade "+str(ii+1)+" of "+str(grade_number)+\
						"...")
				gr['datadrop']=dd_obj
				gr['upn']=student.objects.get(upn=gr['upn'])
				try:
					gr['subject']=subject.objects.get(
						name=gr['Qualification Name'],
						cohort=form.cleaned_data.get('cohort'))
					gr['method']=gr['subject'].method
					if gr['subject'].name=="English Literature":
						class_subject=[gr['subject'],
							subject.objects.get(name="English Language",
							cohort=form.cleaned_data.get('cohort'))]
					elif gr['subject'].name=="English Language":
						class_subject=[gr['subject'],
						subject.objects.get(name="English Literature",
							cohort=form.cleaned_data.get('cohort'))]
					else:
						class_subject=[gr['subject']]
				except:
					"""if any object missing, creates object in database using
					information available"""
					#detemining grade method used for subject
					mtd=gradeMethod.objects.filter(text=gr['Type'])
					if len(mtd)<1:
						mtd=gradeMethod.objects.filter(
							vals__name=gr['Grade'])
					if len(mtd)>=1:
						gr['method']=mtd[0]
						print("<"+str(datetime.datetime.now()).split('.')[0]+\
						">: Assigning method "+gr['method'].text+" to subject "\
						+gr['Qualification Name'])
					#determines various subject values using subject name
					ebacc_bool,option_bool,faculty,bkt=get_subject_type_info(
						gr['Qualification Name'])
					#get or create subject for grade
					gr['subject'],subject_created=subject.objects.get_or_create(
						name=gr['Qualification Name'],
							cohort=form.cleaned_data.get('cohort'),
								defaults={'method':gr['method'],
										'attainment8bucket':bkt,
										'faculty':faculty,
										'ebacc_subject':ebacc_bool,
										'option_subject':option_bool})

					if subject_created:#add to output
						created_subjects.append(gr['subject'].__str__())

					"""for KS4 English subjects, if one is created, also create
					the other, use both in when creating classes"""
					if "English L" in gr['Qualification Name']:
						if "Literature" in gr['Qualification Name']:
							other_subj, subject_created=subject.objects\
							.get_or_create(name="English Language",
								cohort=form.cleaned_data.get('cohort'),
								defaults={'method':gr['method'],
									'attainment8bucket':bkt,
									'faculty':faculty,
									'ebacc_subject':ebacc_bool,
									'option_subject':option_bool})

						elif "Language" in gr['Qualification Name']:
							other_subj, subject_created=subject.objects\
								.get_or_create(name="English Literature",
								cohort=form.cleaned_data.get('cohort'),
								defaults={'method':gr['method'],
									'attainment8bucket':bkt,
									'faculty':faculty,
									'ebacc_subject':ebacc_bool,
									'option_subject':option_bool})
						class_subject=[gr['subject'],other_subj]
						if subject_created:
							created_subjects.append(other_subj.__str__())
					else:
						class_subject=[gr['subject']]
				#retrieve grade value
				try:
					gr_value=gr['Grade']
					if isinstance(gr_value,float):
						gr_value=str(int(gr_value))
					else:
						gr_value=str(gr_value)
					if "=" in gr_value:
						gr_value.replace("=","")
					gr['value']=gr['method'].vals.get(name=gr_value)
				except:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
						str(type(gr['Grade'])))
					print(gr['method'])
					for gv in gr['method'].vals.all():
						print(type(gv.name),gv.name)
					print()
					print()
					raise
				"""get EAP grade associated with datadrop & subject - if
				Combined Science, need to split grade - SISRA returns a
				doubled 9-1 grade"""
				try:
					if isinstance(gr['EAP Grade'],float) or\
					isinstance(gr['EAP Grade'],int):
						gr['EAPgrade']=gradeValue.objects.get(
							name=str(gr['EAP Grade'])[0])

					elif gr['Qualification Name']=='Combined Science' and \
					str(gr['EAP Grade'][:-1]).isnumeric() and \
					"0" not in str(gr['EAP Grade']):
						gr['EAPgrade']=gradeValue.objects.get(
							name=str(gr['EAP Grade'])[1:].replace("=",""))
					else:
						try:
							gr['EAPgrade']=gradeValue.objects.get(
								name=gr['EAP Grade'].replace("=",""))
						except:
							gr['EAPgrade']=gr['method'].vals.get(
									name=gr['EAP Grade'].replace("=",""))
				except:
					pass
				#get baseline grade
				baseline_grade=str(gr['Compare Grade'])
				# if isinstance(baseline_grade,float):
				# 	baseline_grade=str(int(baseline_grade))

				if "=" in str(baseline_grade):
					baseline_grade=str(baseline_grade).replace("=","")
				#calculate progress from baseline grade
				try:
					try:
						gr['baseline_grade']= gr['method'].vals.get(\
						name=baseline_grade)
					except:
						gr['baseline_grade']=gradeMethod.objects.get(text="9-1").\
							vals.get(name=baseline_grade)
						#gr['baseline_grade']=grade.objects.filter(
							#name=baseline_grade)[0]
					gr['progress']=gr['value'].progress_value -\
						gr['baseline_grade'].progress_value
				except:
					print("Empty baseline for " +gr['upn'].surname+", "+\
						gr['upn'].forename + " in " +gr['Qualification Name']+\
						" with entered value " + baseline_grade)
					gr['baseline_grade']=None
					gr['progress']=None

				#handle pupils with multiple classes for one subject
				if "(Multiple)" in gr['Class']:
					gr['staff']=['-']
					gr['Class']=gr['Class']+"-"+gr['subject'].name
					multiple_classes.append(gr['upn'].forename + " "+ gr['upn']\
						.surname+","+gr['subject'].name)
				if len(gr['staff'])>1:
					staff_string=" ".join(gr['staff'])
				else:
					staff_string=gr['staff'][0]
				#get or create correct classgroup for grade
				gr['classgroup'],classgroup_created=classgroup.objects\
					.get_or_create(class_code=gr['Class'],
					cohort=form.cleaned_data.get('cohort'),
						defaults={'staff':staff_string})
				gr['classgroup'].subject=class_subject
				gr['classgroup'].save()
				if classgroup_created:
					created_classes.append(gr['Class'])
				#put formatted grade into new grades dataframe
				new_grades_df.loc[ii]=gr
				#iterate valid grade counter
				ii+=1
			#remove unnecessary columns from new grades dataframe
			new_grades_df.drop(['Qualification Name','Basket','Class','Type',
				'Att8 Points','staff','Compare Grade','Grade','EAP Grade'],
				axis=1,inplace=True)

			print("<"+str(datetime.datetime.now()).split('.')[0]+\
			">: Processing " + str(len(grades_df)) + " imports...")
			#loop through new grades dataframe, save each grade to db
			for i,gr in new_grades_df.iterrows():
				if type(gr['EAPgrade'])!=gradeValue:
					gr['EAPgrade']=None
				selected_grade,grade_created=grade.objects.update_or_create(upn=gr['upn'],
				datadrop=gr['datadrop'],subject=gr['subject'],defaults=gr.to_dict())
				selected_grade.save()

			for i,hd in headlines_df.iterrows():
				try:
					hd['id']=hd['upn']+"/"+hd['datadrop']
					hd['upn']=student.objects.get(upn=hd['upn'])
					hd['datadrop'] =dd_obj
					if str(hd['eb_filled'])=="nan":
						hd['eb_filled']=None
					if str(hd['op_filled'])=="nan":
						hd['op_filled']=None
					try:
						created_headline,was_headline_created=headline.objects.update_or_create(id=hd["id"],defaults=hd.to_dict())
						created_headline.save()
					except:
						pass
				except:
					raise
					failed_headlines.append((hd['upn'],hd['datadrop']))

			#print saved feedback output from relevant lists
			if len(failed_upns)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
				"Importing failed on following Students:")
				for u in failed_upns:
					print(student.objects.get(upn=u))
			if len(failed_headlines)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
				"Importing failed on headline measures for "+ str(len(failed_headlines)) + "students:")
				for h in failed_headlines:
					print(h)
			if len(failed_grades)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  \
					"Importing failed on following grades:")
				for gr in failed_grades:
					print('Grade ' + str(gr['Grade']) + ' for ' + student.\
						objects.get(upn=gr['upn']).__str__() + ' in ' +\
						gr['Qualification Name'])
			if len(created_classes)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+ \
					"The following classes were created:")
				for c in created_classes:
					print(c)
			if len(created_subjects)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  \
				"The following subjects were created:")
				for s in created_subjects:
					print(s)
			if len(multiple_classes)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  \
				"The following students had multiple classes for a subject:")
				for m in multiple_classes:
					print(m)
			try:
				os.remove("lastUnfinishedImportCuY" + cohort + dd_name +".p")
			except:
				pass
			#render page showing imported students, grades
			students_table=students_df.to_html
			grades_table=new_grades_df.to_html
			headlines_table=headlines_df.to_html
			context={'students':students_table,'grades':grades_table,
				'headlines':headlines_table}
			return render(request,'analysis/quickDisplayDF.html',context)
	context={'form':form}
	return render(request,'analysis/importPrompt.html',context)

def interrogate(request):
	from .forms import interrogatorForm
	"""if not POST, renders blank interrogator page, if POST, retrieve and show
	dataframe based on entered query"""
	if request.method !="POST":
		form=interrogatorForm()
	else:
		form=interrogatorForm(data=request.POST)
		if form.is_valid():
			outputTable=get_formatted_output_table(form)
			#outputTable.fillna(value="-",inplace=True)
			if 'export_table' in request.POST:
				filename="scapasQuery-" + str(datetime.datetime.now()).split(".")[0] \
					+ ".xlsx"
				filename=filename.replace(" ","").replace(":","")
				return export_excel(outputTable,filename)
			#change output dataframe table to html format
			outputTable.set_table_attributes('class="table table-striped\
				table-hover table-bordered"')
			outputTable=outputTable.render().replace('nan','')
			#render page with input form and filled table
			context={'form':form,'outputTable':outputTable}
			return render(request,'analysis/interrogatorNew.html',context)
	context={'form':form,'outputTable':""}
	return render(request,'analysis/interrogatorNew.html',context)

def getInterrogatorOutput(form):
	from .forms import interrogatorForm
	"""given valid form from interrogator template, retrieves and formats
	output dataframe"""
	filters={}
	#get individual object filters
	for grp in [('yeargroup','cohort',""),('subject','subject',"name"),\
		('classgroup','classgroup',""),('datadrop','datadrop',"name")]:
		if form.cleaned_data.get(grp[0]+'_selected') and grp[2]!="" and\
		form.cleaned_data.get('match_'+grp[0]+'_by_name')==True:
			filters[grp[1]+"__"+grp[2]]=getattr(
				form.cleaned_data.get(grp[0]+'_selected'),grp[2])
		elif form.cleaned_data.get(grp[0]+"_selected"):
			filters[grp[1]]=form.cleaned_data.get(grp[0]+'_selected')
	#determine filters for rows & columns based on selected values
	if "datadrop__name" in filters:
		if filters['datadrop__name']=="latest":
			filters.pop('datadrop__name')
			if "cohort" in filters:
				filters['datadrop__name']=datadrop.objects.filter(
					cohort=filters['cohort']).latest('date').name
			else:
				dds=[]
				for y in yeargroup.objects.all():
					dds_found=datadrop.objects.filter(cohort=y)
					if dds_found.count()>0:
						dds.append(dds_found.latest('date'))
				if len(dds)>0:
					filters['datadrop__in']=dds
	elif "datadrop" in filters:
		if filters['datadrop']=="latest":
			filters.pop('datadrop')
			if "cohort" in filters:
				filters['datadrop']=datadrop.objects.filter(
					cohort=filters['cohort']).latest('date')
			else:
				dds=[]
				for y in yeargroup.objects.all():
					dds_found=datadrop.objects.filter(cohort=y)
					if dds_found.count()>0:
						dds.append(dds_found.latest('date'))
				if len(dds)>0:
					filters['datadrop__in']=dds
	measure=form.cleaned_data.get('val_choice')
	rfilters=get_default_filters_dict(form.cleaned_data\
		.get('row_choice'),measure,**filters)
	cfilters=get_default_filters_dict(form.cleaned_data\
		.get('col_choice'),measure,**filters)

	#set/edit filters for use directly on grades
	if "cohort" in filters:
		filters['datadrop__cohort']=filters['cohort']
		filters.pop('cohort')
	filters=clean_filters(filters,measure)

	#get dataframe of values matching every combination of filters
	# if measure in ['attainment8','progress8',
	# 	'en_att8','ma_att8','eb_att8','op_att8','eb_filled','op_filled','att8_progress']:
	# 	outputTable=df_measure(avg_measure,rfilters,cfilters,measure=measure,obj=headline,**filters)
	# elif measure in ['meeting','exceeding']:
	# 	if measure=="exceeding":
	# 		outputTable=datadrop.objects.all()[0].pct_EAP_df(True,
	# 			cfilters,rfilters,filters)
	# 	else:
	# 		outputTable=datadrop.objects.all()[0].pct_EAP_df(False,
	# 			cfilters,rfilters,filters)
	# elif measure=="ppGap":
	# 	for g in ["PP","NPP"]:
	# 		for f in [cfilters,rfilters]:
	# 			if g in f:
	# 				f.pop(g,None)
	# 	outputTable=datadrop.objects.all()[0].avg_progress_df_filters_col(
	# 		cfilters,rfilters,**filters,upn__pp=False).replace(to_replace="-",
	# 		value=np.nan)-datadrop.objects.all()[0].\
	# 		avg_progress_df_filters_col(cfilters,rfilters,**filters,
	# 		upn__pp=True).replace(to_replace="-",value=np.nan)
	# elif measure in ['ebacc_entered','ebacc_achieved_std','ebacc_achieved_stg','basics_9to4','basics_9to5']:
	# 	outputTable=datadrop.objects.all()[0].pct_headline_df(
	# 		cfilters,rfilters,filters,measure)
	# else:
	# 	outputTable=datadrop.objects.all()[0].avg_progress_df_filters_col(
	# 		cfilters,rfilters,**filters)

	gap_types={
	    "pp":{
	        "grp_type":"upn__pp",
	        "grpA_values":False,
	        "grpB_values":True,
	    },
	    "sen":{
	        "grp_type":"upn__sen",
	        "grpA_values":"N",
	        "grpB_values":["E","K"],
	    },
	    "fsm_ever":{
	        "grp_type":"upn__fsm_ever",
	        "grpA_values":False,
	        "grpB_values":True,
	    },
	    "gen":{
	        "grp_type":"upn__gender",
	        "grpA_values":"M",
	        "grpB_values":"F",
	    },
	    "eal":{
	        "grp_type":"upn__eal",
	        "grpA_values":False,
	        "grpB_values":True,
	    },
	    "lac":{
	        "grp_type":"upn__lac",
	        "grpA_values":False,
	        "grpB_values":True,
	    },
	    "hst":{},
	}

	#set comparison and alter measure for measures that don't directly correspond to
	#filter quantities
	comparison=None
	if measure =="ach_eap":
	    measure="value__progress_value"
	    comparison="EAPgrade__progress_value"
	elif measure=="passing":
	    measure="value__progress_value"
	    comparison="method__pass_grade__progress_value"
	elif measure=="ach_progress":
	    measure="progress"
	    comparison=0.001
	elif measure in ['ebacc_entered','ebacc_achieved_std','ebacc_achieved_stg',
	'basics_9to4','basics_9to5']:
	    comparison=True

	filters['obj']=get_measure_obj(measure)
	filters['measure']=measure
	if comparison:
	    filters['comparison']=comparison

	student_residual=form.cleaned_data.get('student_residual')
	if form.cleaned_data.get('only_exceeding'):
		filters['only_exceeding']=form.cleaned_data.get('only_exceeding')

	#set base function
	if not comparison is None:
	    function=pct_measure
	elif student_residual:
	    function=residual_measure
	else:
	    function=avg_measure



	# if gap, set function as gap_measure and calc function as base function
	if form.cleaned_data.get('calc_gap'):
	    filters={**filters,**gap_types[form.cleaned_data.get('gap_type')]}
	    filters['calc_function']=function
	    function=gap_measure

	outputTable=df_measure(function,rfilters,cfilters,**filters)

	#format & apply colour coding
	outputTable.replace(to_replace="-",value=np.nan,inplace=True)
	if form.cleaned_data.get('residual_toggle_col'):
		#for residual, create mask of "All" values and subtract from df
		residual_mask=pd.DataFrame()
		residual_mask['All']=outputTable['All']
		for c in outputTable.columns:
			residual_mask[c]=outputTable['All']
		outputTable=outputTable-residual_mask
	if form.cleaned_data.get('residual_toggle_row'):
		#for residual, create mask of "All" values and subtract from df
		residual_mask=pd.DataFrame(columns=outputTable.columns)
		residual_mask.loc['All']=outputTable.loc['All']
		for c in outputTable.index.values:
			residual_mask.loc[c]=outputTable.loc['All']
		outputTable=outputTable-residual_mask
	return outputTable

def get_formatted_output_table(form):
	from .forms import interrogatorForm
	outputTable=getInterrogatorOutput(form)
	if form.cleaned_data.get("val_choice")!="ppGap":
		if (form.cleaned_data.get('residual_toggle_row') and form.cleaned_data.get('residual_toggle_col')) or (not form.cleaned_data.get('residual_toggle_row') and not form.cleaned_data.get('residual_toggle_col')):
			outputTable=outputTable.style.apply(colour_progress_df,axis=None)
			#outputTable=outputTable.style.bar(align='mid',color=['red','green'])

		elif form.cleaned_data.get('residual_toggle_row'):
			outputTable=outputTable.style.apply(colour_progress,axis=0)
		else:
			outputTable=outputTable.style.apply(colour_progress,axis=1)

	else:
		if (form.cleaned_data.get('residual_toggle_row') and form.cleaned_data.get('residual_toggle_col')) or (not form.cleaned_data.get('residual_toggle_row') and not form.cleaned_data.get('residual_toggle_col')):
			outputTable=outputTable.style.apply(colour_pp_gap_df,axis=None)
		elif form.cleaned_data.get('residual_toggle_row'):
			outputTable=outputTable.style.apply(colour_pp_gap,axis=0)
		else:
			outputTable=outputTable.style.apply(colour_pp_gap,axis=1)

	outputTable=outputTable.highlight_null(null_color="grey")
	return outputTable

def get_standard_table(view_focus,view_rows,view_cols,cohort="",
start_dd="",**filters):
	if "name" in filters:
		filters[view_focus+"__name"]=filters.pop("name")

	#get row filters
	if cohort:
		row_filters=get_default_filters_dict(view_rows,"progress",cohort=cohort,
			**filters)
	else:
		row_filters=get_default_filters_dict(view_rows,"progress",**filters)

	#create output dataframe and list of filter sets for columns
	out=pd.DataFrame()
	if cohort and view_cols!="analysis":
		datadrop_list=datadrop.objects.filter(cohort=cohort)\
			.order_by('-date')[:3][::-1]
	elif view_cols=="analysis":
		datadrop_list=datadrop.objects.filter(cohort=cohort)\
			.order_by('-date')[:2]
	else:
		datadrop_list=None

	if "class_code" in filters :
		filters["classgroup__class_code"]=filters.pop("class_code")

	#for each entry in column filter list, calculate and insert column series
	#	into output df

	if view_cols=="progress":
		if datadrop_list:
			for dd in datadrop_list:
				out[dd.name+" Avg Progress"]=series_measure(avg_measure,row_filters,
					datadrop=dd,measure="progress",obj=grade,**filters)
				out[dd.name+" Group Diff."]=out[dd.name +" Avg Progress"]-out.\
					loc["All",dd.name +" Avg Progress"]
				out[dd.name +" Residual"]=series_measure(residual_measure,
					row_filters,datadrop=dd,measure="progress",obj=grade,**filters)
		else:
			out["Avg Progress"]=series_measure(avg_measure,row_filters,
				measure="progress",obj=grade,**filters)
			out["Group Diff."]=out["Avg Progress"]-out.\
				loc["All","Avg Progress"]
			out["Residual"]=series_measure(residual_measure,
				row_filters,measure="progress",obj=grade,**filters)
	elif view_cols=="sheet":
		out['#']=series_measure(count_measure,row_filters,
		datadrop=datadrop_list[-1],obj=grade,**filters)
		out['Avg Baseline Attainment Score']=series_measure(avg_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="baseline_grade__att8_value",obj=grade,**filters)
		if len(datadrop_list)>1:
			out['Avg '+datadrop_list[1].name + ' Attainment Score']=\
				series_measure(avg_measure,row_filters,
				datadrop=datadrop_list[1],obj=grade,
				measure="value__att8_value",**filters)
		out['Avg '+datadrop_list[0].name + ' Attainment Score']=series_measure(
			avg_measure,row_filters, datadrop=datadrop_list[0],
			measure="value__att8_value",obj=grade,**filters)
		out['Avg Estimated Attainment Score']=series_measure(avg_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="EAPgrade__att8_value",obj=grade,**filters)
		out['Residual Attainment Score']=series_measure(residual_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="value__att8_value",obj=grade,**filters)
		out['Avg Baseline Attainment +=- Score']=series_measure(avg_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="baseline_grade__progress_value",obj=grade,**filters)
		if len(datadrop_list)>1:
			out['Avg '+datadrop_list[1].name + ' Attainment +=- Score']=\
				series_measure(avg_measure,row_filters,
				datadrop=datadrop_list[1],obj=grade,
				measure="value__progress_value",**filters)
		out['Avg '+datadrop_list[0].name + ' Attainment +=- Score']=\
			series_measure(avg_measure,row_filters, datadrop=datadrop_list[0],
			measure="baseline_grade__progress_value",obj=grade,**filters)
		out['Avg Estimated Attainment +=- Score']=series_measure(avg_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="EAPgrade__progress_value",obj=grade,**filters)
		out['Residual Attainment +=- Score']=series_measure(residual_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="value__progress_value",obj=grade,**filters)
		if len(datadrop_list)>1:
			out['Avg '+datadrop_list[1].name + ' Attainment +=- Score']=\
				series_measure(avg_measure,row_filters,
				datadrop=datadrop_list[1],obj=grade,
				measure="value__progress_value",**filters)
		out['Avg '+datadrop_list[0].name + ' Attainment +=- Score']=\
			series_measure(avg_measure,row_filters, datadrop=datadrop_list[0],
			measure="value__progress_value",obj=grade,**filters)
		out['Avg Estimate Attainment +=- Score']=series_measure(avg_measure,
			row_filters, datadrop=datadrop_list[0],
			measure="EAPgrade__progress_value",obj=grade,**filters)
		if len(datadrop_list)>1:
			out['Avg '+datadrop_list[1].name + ' Progress Score']=\
				series_measure(avg_measure,row_filters,
				datadrop=datadrop_list[1],obj=grade,
				measure="progress",**filters)
		out['Avg '+datadrop_list[0].name + ' Progress Score']=\
			series_measure(avg_measure,row_filters,
			datadrop=datadrop_list[0],obj=grade,
			measure="progress",**filters)
		out['Residual Progress']=\
			series_measure(residual_measure,row_filters,
			datadrop=datadrop_list[0],measure="progress",obj=grade,**filters)
		out=avg_grade_filter_points(out)
	elif view_cols=="attainment":
		if datadrop_list:
			for dd in datadrop_list:
				out['% >= Estimates '+ dd.name]=series_measure(pct_measure,
					row_filters,datadrop=dd, measure="value__progress_value",
					comparison="EAPgrade__progress_value",obj=grade,**filters)
				out['% > Estimates '+ dd.name]=series_measure(pct_measure,
					row_filters,datadrop=dd, measure="value__progress_value",
					comparison="EAPgrade__progress_value",obj=grade,
					only_exceeding=True,**filters)
		else:
			out['% >= Estimates']=series_measure(pct_measure,
				row_filters, measure="value__progress_value",
				comparison="EAPgrade__progress_value",obj=grade,**filters)
			out['% > Estimates']=series_measure(pct_measure,
				row_filters, measure="value__progress_value",
				comparison="EAPgrade__progress_value",obj=grade,
				only_exceeding=True,**filters)
	elif view_cols=="headline":
		filters=clean_filters(filters)
		for row in row_filters:
			row_filters[row]=clean_filters(row_filters[row])
		if datadrop_list:
			for dd in datadrop_list:
				out[dd.name+" Avg. Total Attainment 8"]=series_measure(
					avg_measure, row_filters,measure="attainment8",obj=headline,
					datadrop=dd,**filters
				)
				out[dd.name+" Avg. Progress 8"]=series_measure(
					avg_measure,row_filters,measure="progress8",obj=headline,
					datadrop=dd,**filters
				)
		else:
			out["Avg. Total Attainment 8"]=series_measure(
				avg_measure, row_filters,measure="attainment8",obj=headline,
				**filters
			)
			out["Avg. Progress 8"]=series_measure(
				avg_measure,row_filters,measure="progress8",obj=headline,
				**filters
			)
	return out

def stdTable_gen_getsession(request,focus,row_type,col_type):
	request.session['row_type']=row_type
	request.session['col_type']=col_type
	if "subject_selected" not in request.session:
		request.session['subject_selected']=""

	if "yeargroup_selected" not in request.session:
		request.session['yeargroup_selected']=""

	if "classgroup_selected" not in request.session:
		request.session['classgroup_selected']=""

	if "datadrop_selected" not in request.session:
		request.session['datadrop_selected']=""

	return HttpResponseRedirect('/view/'+focus+'/')

def stdTable_gen(request,focus):
	from .forms import standardTableForm_subject,standardTableForm_classgroup,\
		standardTableForm_datadrop
	form=""
	if request.method!="POST":
		outputTable=""
		if focus == "subject":
			form=standardTableForm_subject()
		elif focus == "classgroup":
			form=standardTableForm_classgroup()
		elif focus == "datadrop":
			form=standardTableForm_datadrop()
	else:

		if focus == "subject":
			form=standardTableForm_subject(data=request.POST)
		elif focus == "classgroup":
			form=standardTableForm_classgroup(data=request.POST)
		elif focus == "datadrop":
			form=standardTableForm_datadrop(data=request.POST)

		request.session['yeargroup_selected']=""
		request.session['subject_selected']=""
		request.session['classgroup_selected']=""
		request.session['datadrop_selected']=""
		if form.is_valid():
			request.session['subject_selected']=form.cleaned_data.get(
				"subject_selected")
			request.session['yeargroup_selected']=form.cleaned_data.get(
				'yeargroup_selected')
			request.session['classgroup_selected']=form.cleaned_data.get(
				"classgroup_selected")
			request.session['datadrop_selected']=form.cleaned_data.get(
				"datadrop_selected")
			outputTable,outputTableSt=get_formatted_standard_view_table(request,focus)
			if "export_table" in request.POST:
				filename="scapasStdView-" + str(datetime.datetime.now()).split(".")[0] \
					+ ".xlsx"
				filename=filename.replace(" ","").replace(":","")
				return export_excel(outputTableSt,filename)
			try:
				outputTable=outputTableSt.render().replace('nan','')
			except TypeError as err:
				print(outputTable)
				print(err)
				outputTable=outputTable.to_html().replace('nan','')
		else:
			outputTable="Form not valid :("
	context={'form':form,'outputTable':outputTable,
		'row_type':request.session['row_type'],
		'col_type':request.session['col_type'],
		'subject_selected':request.session['subject_selected'],
		'yeargroup_selected':request.session['yeargroup_selected'],
		'classgroup_selected':request.session['classgroup_selected'],
		'datadrop_selected':request.session['datadrop_selected'],
	}
	template=""
	if focus=="subject":
		template="analysis/stdTableSub.html"
	elif focus=="classgroup":
		template="analysis/stdTableCls.html"
	elif focus=="datadrop":
		template="analysis/stdTableDdp.html"
	return render(request,template,context)

def get_formatted_standard_view_table(request,focus):
	if request.session['row_type']=="yeargroup":
		year=""
	else:
		year=yeargroup.objects.get(cohort=\
			request.session['yeargroup_selected'][0:9])
	if focus=="subject":
		pass_filters={'name':request.session['subject_selected']}
	elif focus=="classgroup":
		pass_filters={'class_code':request.session['classgroup_selected'],
			'subject__name':request.session['subject_selected'],
			}
	elif focus=="datadrop":
		pass_filters={}
		if request.session['row_type']!="yeargroup":
			pass_filters['name']=request.session['datadrop_selected']
		if request.session['subject_selected']!="":
			pass_filters['subject__name']=request.session['subject_selected']
		if request.session['classgroup_selected']!="":
			pass_filters['classgroup__class_code']=request.session['classgroup_selected']

	outputTable=get_standard_table(focus,request.session['row_type'],
		request.session['col_type'],year,**pass_filters)
	if request.session['col_type']=="attainment":
		outputTableSt=outputTable.style.apply(colour_mx_EAP,axis=0)
	elif request.session['col_type']=="sheet":
		outputTableSt=outputTable.style.apply(colour_progress,axis=0)
	else:
		outputTableSt=outputTable.style.apply(colour_progress,axis=0)
	outputTableSt.set_table_attributes('class="table table-striped\
	 table-hover table-bordered"')
	return outputTable,outputTableSt

def getLatestDatadropPerYeargroup():
	row_filter=[]
	for y in yeargroup.objects.all().order_by('-current_year'):
		dd=datadrop.objects.filter(cohort=y)
		if dd.count()>0:
			dd=dd.order_by('-date')[0]
			row_filter.append(dd)
			#row_filter[y.__str__()+", "+dd.name]={'upn__cohort':y,'datadrop':dd}
	return row_filter

def export_excel(output_data,filename):
	sio=io.BytesIO()
	writer=pd.ExcelWriter(sio,engine='openpyxl')

	output_data.to_excel(writer,sheet_name="Sheet1")
	writer.save()

	sio.seek(0)
	workbook=sio.getvalue()


	response= HttpResponse(workbook,
		content_type='application/vnd.ms-excel')
	response['Content-Disposition']='attachment; filename="' +\
		filename + '"'
	return response
