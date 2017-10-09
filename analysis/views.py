from django.shortcuts import render
from .models import *
from .sisraTools import *
from selenium import webdriver
from .forms import importForm,interrogatorForm,standardTableForm_subject,\
	standardTableForm_classgroup
from django.http import HttpResponseRedirect,HttpResponse
from assessment import settings
import sqlite3
import time
import pandas as pd
import numpy as np
from .colourCodingRules import colour_progress,colour_pp_gap,colour_pp_gap_df,colour_progress_df,colour_mx_EAP
import seaborn as sns
import io
from django.apps import apps
import pickle
import os
#from data_interrogator import views

# Create your views here.

def index(request):
	"""renders home page for assessment tools"""
	return render(request, 'analysis/index.html')

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
				'classgroup','datadrop','value','EAPgrade'])

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
							vals__name__contains=gr['Grade'])
					if len(mtd)>=1:
						gr['method']=mtd[0]
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
					gr['value']=gr['method'].vals.get(name=gr_value)
				except:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
						type(gr['Grade']))
					print(gr['method'])
					for gv in gr['method'].vals.all():
						print(type(gv.name),gv.name)
					print()
					print()
					raise
				"""get EAP grade associated with datadrop & subject - if
				Combined Science, need to split grade - SISRA returns a
				doubled 9-1 grade"""
				if isinstance(gr['EAP Grade'],float):
					gr['EAPgrade']=gradeValue.objects.get(
						name=str(gr['EAP Grade'])[0])

				elif gr['Qualification Name']=='Combined Science' and \
				str(gr['EAP Grade']).isnumeric():
					gr['EAPgrade']=gradeValue.objects.get(
						name=str(gr['EAP Grade'])[0])
				else:
					gr['EAPgrade']=gradeValue.objects.get(name=gr['EAP Grade'])
				#get baseline grade
				baseline_grade=gr['Compare Grade']
				if isinstance(baseline_grade,float):
					baseline_grade=str(int(baseline_grade))
				#calculate progress from baseline grade
				try:
					gr['progress']=gr['value'].progress_value - gr['method'] \
					.vals.get(name=baseline_grade).progress_value
				except:
					raise
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
						defaults={'cohort':form.cleaned_data.get('cohort'),
							'staff':staff_string,'subject':class_subject})
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
	"""if not POST, renders blank interrogator page, if POST, retrieve and show
	dataframe based on entered query"""
	if request.method !="POST":
		form=interrogatorForm()
	elif 'export_table' in request.POST:
		return interrogateExport(request)
	else:
		form=interrogatorForm(data=request.POST)
		if form.is_valid():
			outputTable=get_formatted_output_table(form)
			#outputTable.fillna(value="-",inplace=True)

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
	if measure in ['attainment8','progress8',
		'en_att8','ma_att8','eb_att8','op_att8','eb_filled','op_filled','att8_progress']:
		outputTable=datadrop.objects.all()[0].avg_headline_df(
			cfilters,rfilters,filters,measure)
	elif measure in ['meeting','exceeding']:
		if measure=="exceeding":
			outputTable=datadrop.objects.all()[0].pct_EAP_df(True,
				cfilters,rfilters,filters)
		else:
			outputTable=datadrop.objects.all()[0].pct_EAP_df(False,
				cfilters,rfilters,filters)
	elif measure=="ppGap":
		for g in ["PP","NPP"]:
			for f in [cfilters,rfilters]:
				if g in f:
					f.pop(g,None)
		outputTable=datadrop.objects.all()[0].avg_progress_df_filters_col(
			cfilters,rfilters,**filters,upn__pp=False).replace(to_replace="-",
			value=np.nan)-datadrop.objects.all()[0].\
			avg_progress_df_filters_col(cfilters,rfilters,**filters,
			upn__pp=True).replace(to_replace="-",value=np.nan)
	elif measure in ['ebacc_entered','ebacc_achieved_std','ebacc_achieved_stg','basics_9to4','basics_9to5']:
		outputTable=datadrop.objects.all()[0].pct_headline_df(
			cfilters,rfilters,filters,measure)
	else:
		outputTable=datadrop.objects.all()[0].avg_progress_df_filters_col(
			cfilters,rfilters,**filters)
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

def interrogateExport(request):
	"""takes POST request and serves excel file of returned dataframe"""
	form=interrogatorForm(data=request.POST)
	if form.is_valid():
		filename="scapasQuery-" + str(datetime.datetime.now()).split(".")[0] \
			+ ".xlsx"
		filename=filename.replace(" ","").replace(":","")
		sio=io.BytesIO()
		writer=pd.ExcelWriter(sio,engine='openpyxl')

		outputTable=get_formatted_output_table(form)

		outputTable.to_excel(writer,sheet_name="Sheet1")
		writer.save()

		sio.seek(0)
		workbook=sio.getvalue()


		response= HttpResponse(workbook,
			content_type='application/vnd.ms-excel')
		response['Content-Disposition']='attachment; filename="' +\
			filename + '"'
		return response

def get_formatted_output_table(form):
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
	"""view focus can be "classgroup", "subject" or "datadrop".
	rows can be "student" (VGs),"classgroup","yeargroup", "datadrop",
	or "subject".
	columns can be "progress","attainment" (EAP), "headline" (A8/P8) or
	(for datadrops) "all" ."""


	if view_rows!="yeargroup" and cohort!="":
		filters['cohort']=cohort

	#get focus object and datadrop (if applicable)

	focus_model=apps.get_model(model_name=view_focus,app_label="analysis")
	focus_object=focus_model.objects.filter(**filters)[0]
	if view_focus=="classgroup":
		focus_label=focus_object.class_code
	else:
		focus_label=focus_object.name

	if "name" in filters.keys(): #and view_focus=="subject":
		filters[view_focus + "__name"]=filters.pop('name')
	#elif "name" in filters.keys() and view_focus=="datadrop":
		#filters.pop('name')
	if "class_code" in filters.keys():
		filters[view_focus]=filters.pop('class_code')
	if view_cols=="headline" and view_focus=="subject" and view_rows!="yeargroup":
		filters['upn__grade__' + view_focus]=focus_object
	elif view_rows!="yeargroup":
		filters[view_focus]=focus_object
	if view_rows=="student" and "cohort" in filters.keys():
		filters["upn__cohort"]=cohort
		filters.pop("cohort")

	output_df=pd.DataFrame()

	#get row filter conditions
	if view_cols == "headline":
		measure="progress8"
	else:
		measure=view_cols
	row_filters=get_default_filters_dict(view_rows,measure,**filters)
	if view_cols=="headline" and view_focus!="datadrop":
		filters['upn__grade__' + view_focus]=focus_object
		filters.pop(view_focus)

	if "upn__cohort" not in filters.keys() and "cohort" in filters.keys():
		filters["upn__cohort"]=cohort
		filters.pop("cohort")

	#set columns
	if view_focus=="datadrop" or view_rows=="yeargroup":
		if view_rows=="yeargroup":
			new_rf={"All":{}}
			for y,inner_dict in row_filters.items():
				for val in inner_dict.values():
					new_rf[y]={'datadrop':datadrop.objects.filter(cohort=val).order_by("date")[0]}
			row_filters=new_rf
		if view_cols=="progress" or view_cols=="all":
			output_df[focus_label + " Avg Progress"] =\
				focus_object.avg_progress_series(group_filters_dict=row_filters,filters=filters)
			#avg=output_df[focus_object.name +" Avg Progress"].mean()
			#output_df[focus_object.name +" Residual"] = \
				#output_df[focus_object.name+" Avg Progress"] - output_df.loc["All",focus_object.name+" Avg Progress"]
			for i in output_df.index:
				try:
					output_df.loc[i,focus_label +" Residual"]=\
					output_df.loc[i,focus_label +" Avg Progress"] -\
					output_df.loc["All",focus_label +" Avg Progress"]
				except:
					output_df.loc[i,focus_label +" Residual"]=""
		if view_cols=="attainment" or view_cols=="all":
			output_df[focus_label+" >=EAP"]=\
				focus_object.pct_EAP_series(False,row_filters,filters)
			output_df[focus_label+" >EAP"]=\
				focus_object.pct_EAP_series(True,row_filters,filters)

		if view_cols=="headline" or view_cols=="all":
			output_df[focus_label+" Att8"]=\
				focus_object.avg_headline_series(row_filters,filters,"attainment8")
			output_df[focus_label+" P8"]=\
				focus_object.avg_headline_series(row_filters,filters,"progress8")
	else:
		# get starting datadrop & get list of datadrops to use
		if start_dd=="":
			start_dd="Y7 DD2"
		start_dd=datadrop.objects.filter(cohort=cohort,
			name=start_dd).first()
		if start_dd is None:
			start_dd=datadrop.objects.filter(cohort=cohort).order_by('date')[0]
		datadrops=datadrop.objects.filter(date__gte=start_dd.date,cohort=cohort).order_by('date')
		if len(datadrops)>=3:
			datadrops=list(datadrops)[-3:]
		#populate dataframe
		if view_cols=="progress":
			for d in datadrops:
				filters['datadrop']=d
				output_df[d.name + " Avg Progress"] =\
					focus_object.avg_progress_series(group_filters_dict=row_filters,filters=filters)
				#avg=output_df[d.name +" Avg Progress"].mean()
				# output_df[d.name +" Residual"] = \
					# output_df[d.name+" Avg Progress"] - output_df.loc["All",d.name+" Avg Progress"]
				for i in output_df.index:
					try:
						output_df.loc[i,d.name +" Residual"]=\
						output_df.loc[i,d.name +" Avg Progress"] -\
						output_df.loc["All",d.name +" Avg Progress"]
					except:
						output_df.loc[i,d.name +" Residual"]="-"

		elif view_cols=="attainment":
			for d in datadrops:
				filters['datadrop']=d
				output_df[d.name+" >=EAP"]=\
					focus_object.pct_EAP_series(False,row_filters,filters)
				output_df[d.name+" >EAP"]=\
					focus_object.pct_EAP_series(True,row_filters,filters)

		elif view_cols=="headline":
			for d in datadrops:
				filters['datadrop']=d
				output_df[d.name+" Att8"]=\
					focus_object.avg_headline_series(row_filters,filters,"attainment8")
				output_df[d.name+" P8"]=\
					focus_object.avg_headline_series(row_filters,filters,"progress8")
	output_df=output_df.reindex(index=row_filters.keys())
	return output_df

def stdTable_sub_getsession(request,row_type,col_type):
	request.session['row_type']=row_type
	request.session['col_type']=col_type
	if "subject_selected" not in request.session:
		request.session['subject_selected']=""

	if "yeargroup_selected" not in request.session:
		request.session['yeargroup_selected']=""

	if "classgroup_selected" not in request.session:
		request.session['classgroup_selected']=""

	return HttpResponseRedirect('/view/subject/')

def stdTable_gen_getsession(request,focus,row_type,col_type):
	request.session['row_type']=row_type
	request.session['col_type']=col_type
	if "subject_selected" not in request.session:
		request.session['subject_selected']=""

	if "yeargroup_selected" not in request.session:
		request.session['yeargroup_selected']=""

	if "classgroup_selected" not in request.session:
		request.session['classgroup_selected']=""

	return HttpResponseRedirect('/view/'+focus+'/')

def stdTable_sub(request):
	if request.method!="POST":
		form=standardTableForm_subject()
		outputTable=""
	else:
		form=standardTableForm_subject(data=request.POST)
		request.session['yeargroup_selected']=""
		request.session['subject_selected']=""
		if form.is_valid():
			request.session['subject_selected']=form.cleaned_data.get("subject_selected")
			if request.session['row_type']=="yeargroup":
				year=""
			else:
				request.session['yeargroup_selected']=form.cleaned_data.get("yeargroup_selected")
				year=yeargroup.objects.get(cohort=form.cleaned_data.get("yeargroup_selected")[0:9])
			outputTable=get_standard_table("subject",request.session['row_type'],request.session['col_type'],
				year,name=form.cleaned_data.get("subject_selected"))
			#outputTable.replace(to_replace='-',value=float(''),inplace=True)
			if request.session['col_type']=="attainment":
				outputTableSt=outputTable.style.apply(colour_mx_EAP,axis=0)
			else:
				outputTableSt=outputTable.style.apply(colour_progress,axis=0)
			outputTableSt.set_table_attributes('class="table table-striped\
			 table-hover table-bordered"')
			try:
				outputTable=outputTableSt.render().replace('nan','')
			except TypeError as err:
				print(outputTable)
				print(err)
				outputTable=outputTable.to_html
	context={'form':form,'outputTable':outputTable,'row_type':request.session['row_type'],'col_type':request.session['col_type'],'subject_selected':request.session['subject_selected'],'yeargroup_selected':request.session['yeargroup_selected']}
	return render(request,'analysis/stdTableSub.html',context)

def stdTable_cls(request):
	if request.method!="POST":
		form=standardTableForm_classgroup()
		outputTable=""
	else:
		form=standardTableForm_subject(data=request.POST)
		#set session variables
		request.session['yeargroup_selected']=""
		request.session['subject_selected']=""
		request.session['classgroup_selected']=""
		if form.is_valid():
			request.session['subject_selected']=form.cleaned_data.get("subject_selected")
			request.session['yeargroup_selected']=form.cleaned_data.get('yeargroup_selected')
			request.session['classgroup_selected']=form.cleaned_data.get("classgroup_selected")
			year=yeargroup.objects.get(cohort=request.session['yeargroup_selected'][0:9])
			outputTable=get_standard_table("classgroup",request.session['row_type'],
				request.session['col_type'],year,
				subject__name=form.cleaned_data.get("subject_selected"),
				class_code=form.cleaned_data.get("classgroup_selected"))
			if request.session['col_type']=="attainment":
				outputTableSt=outputTable.style.apply(colour_mx_EAP,axis=0)
			else:
				outputTableSt=outputTable.style.apply(colour_progress,axis=0)
			outputTableSt.set_table_attributes('class="table table-striped table-hover table-bordered"')
			try:
				outputTable=outputTableSt.render().replace('nan','')
			except TypeError as err:
				print(outputTable)
				print(err)
				outputTable=outputTable.to_html
	context={'form':form,'outputTable':outputTable,'row_type':request.session['row_type'],'col_type':request.session['col_type'],'subject_selected':request.session['subject_selected'],'yeargroup_selected':request.session['yeargroup_selected'],'classgroup_selected':request.session['classgroup_selected']}
	return render(request,'analysis/stdTableCls.html',context)
def stdTable_gen(request,focus):
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
		if form.is_valid():
			request.session['subject_selected']=form.cleaned_data.get(
				"subject_selected")
			if request.session['row_type']=="yeargroup":
				year=""
			else:
				request.session['yeargroup_selected']=form.cleaned_data.get(
					'yeargroup_selected')
				year=yeargroup.objects.get(cohort=request.session['yeargroup_selected'][0:9])
			request.session['classgroup_selected']=form.cleaned_data.get(
				"classgroup_selected")
			if focus=="subject":
				pass_filters={'name':request.session['subject_selected']}
			elif focus=="classgroup":
				pass_filters={'class_code':request.session['classgroup_selected'],
					'subject__name':request.session['subject_selected'],
					}
			elif focus=="datadrop":
				pass_filters={}
			outputTable=get_standard_table(focus,request.session['row_type'],
				request.session['col_type'],year,**pass_filters)
			if request.session['col_type']=="attainment":
				outputTableSt=outputTable.style.apply(colour_mx_EAP,axis=0)
			else:
				outputTableSt=outputTable.style.apply(colour_progress,axis=0)
			outputTableSt.set_table_attributes('class="table table-striped\
			 table-hover table-bordered"')
			try:
				outputTable=outputTableSt.render().replace('nan','')
			except TypeError as err:
				print(outputTable)
				print(err)
				outputTable=outputTable.to_html().replace('nan','')
	context={'form':form,'outputTable':outputTable,
		'row_type':request.session['row_type'],
		'col_type':request.session['col_type'],
		'subject_selected':request.session['subject_selected'],
		'yeargroup_selected':request.session['yeargroup_selected'],
		'classgroup_selected':request.session['classgroup_selected']
	}
	template=""
	if focus=="subject":
		template="analysis/stdTableSub.html"
	elif focus=="classgroup":
		template="analysis/stdTableCls.html"
	elif focus=="datadrop":
		template="analysis/stdTableDdp.html"
	return render(request,template,context)
