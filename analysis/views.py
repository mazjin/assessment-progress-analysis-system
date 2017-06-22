from django.shortcuts import render
from .models import *
from .sisraTools import *
from selenium import webdriver
from .forms import importForm
from django.http import HttpResponseRedirect
from assessment import settings
import sqlite3
import time
#from data_interrogator import views

# Create your views here.
def index(request):
	"""home page for assessment tools"""
	return render(request, 'analysis/index.html')
def yeargroups(request):
	"""Lists all cohorts with available data."""
	yeargroups=yeargroup.objects.all()
	context={'yeargroups':yeargroups}
	return render(request, 'analysis/yeargroups.html',context)
def yeargroupClasses(request,cohort_string):
	"""lists all classgroups for a cohort"""
	selected_yeargroup=yeargroup.objects.get(cohort=cohort_string)
	classes=selected_yeargroup.classgroup_set.order_by('subject','class_code')
	context={'cohort':selected_yeargroup,'classes':classes}
	return render(request,'analysis/yeargroupByClasses.html',context)
	
def importPrompt(request):
	if request.method !="POST":
		form=importForm()
	else:
		form=importForm(data=request.POST)
		if form.is_valid():
			username=form.cleaned_data.get('username')
			pw=form.cleaned_data.get('pw')
			cohort=form.cleaned_data.get('cohort').current_year
			dd_name=form.cleaned_data.get('dd_name').name
			browser=webdriver.Chrome()
			logIntoSISRA(username,pw,browser)
			openStudentReports(browser,cohort,dd_name)
			students_df,grades_df=getStudentData(browser,cohort,dd_name)
			students_df['cohort']=form.cleaned_data.get('cohort')

			
			browser.close()
			print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "Student records retrieved, importing...")
			failed_upns=[]
			failed_grades=[]
			created_classes=[]
			created_subjects=[]
			multiple_classes=[]
			student_position=1
			student_number=len(students_df.index)
			student_milestone=int(student_number/15)
			if student_milestone<2:
				student_milestone=1
			for u,stu in students_df.iterrows():
				if student_position % student_milestone==1:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "Importing " + str(student_position) + " of " + str(student_number) + " students...")
				try:
					if stu['banding']=="Lower":
						band="L"
					elif stu['banding']=="Upper/High":
						band="H"
					elif stu['banding']=="Middle":
						band="M"
					else:
						band="N"
					reggroup,reg_created=classgroup.objects.get_or_create(class_code="CLS"+stu['reg'].strip(),defaults={'cohort':form.cleaned_data.get('cohort'),'staff':"---"})
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
						sen=stu['sen'],
						lac=stu['lac']=="Yes",
						fsm_ever=stu['fsm_ever']=="Yes")
					created_student.save()
					if reg_created:
						created_classes.append(created_student.reg.class_code)
					student_position+=1
				# importation attempt: SQL
				#--------
				# engine_url=settings.DATABASES['default']['NAME']
				# engine = sqlite3.connect(engine_url)
				
				# students_df.to_sql(student, con=engine)
				# grades_df.to_sql(grade,con=engine)
				
				#---------------------------------------------
				
				# importation attempt: bulk_create
				#-------
				# students_df['pk']=students_df['upn'].values
				# student_entries=students_df.to_dict('records')
				# print(student_entries)
				# student.objects.bulk_create(student_entries)
				# grade_entries=grades_df.to_dict('records')
				# grade.objects.bulk_create(grade_entries)
				except:
					failed_upns.append(u)
			
			
			new_grades_df=pd.DataFrame(columns=['upn','Qualification Name','Basket','Class','Type','Grade','Att8 Points','EAP Grade','staff','Compare Grade','progress','method','subject','classgroup','datadrop','value','EAPgrade'])
			ii=0
			grade_number=len(grades_df.index)
			grade_milestone=int(grade_number/15)
			if grade_milestone<2:
				grade_milestone=1
			for i, gr in grades_df.iterrows():
				if ii % grade_milestone==0:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "Importing grade " + str(ii+1) +" of "+str(grade_number)+"...")
				gr['datadrop']=form.cleaned_data.get('dd_name')
				gr['upn']=student.objects.get(upn=gr['upn'])
				try:
					gr['subject']=subject.objects.get(name=gr['Qualification Name'],cohort=form.cleaned_data.get('cohort'))
					gr['method']=gr['subject'].method
				except:
					if "English" in gr['Qualification Name']:
						bkt="en"
					elif "Math" in gr['Qualification Name']:
						bkt="ma"
					elif "Science" in gr['Qualification Name'] or gr['Qualification Name'] in ["History","Geography","French","Spanish","MFL"]:
						bkt="eb"
					else:
						bkt="op"
					mtd=gradeMethod.objects.filter(text=gr['Type'])
					if len(mtd)<1:
						mtd=gradeMethod.objects.filter(vals__name__contains=gr['Grade'])
					if len(mtd)>=1:
						gr['method']=mtd[0]
					gr['subject'],subject_created=subject.objects.get_or_create(name=gr['Qualification Name'],cohort=form.cleaned_data.get('cohort'),defaults={'method':gr['method'],'attainment8bucket':bkt})
					if subject_created:
						created_subjects.append(gr['subject'].__str__())
				try:
					gr_value=gr['Grade']
					if isinstance(gr_value,float):
						gr_value=str(int(gr_value))
					else:
						gr_value=str(gr_value)
					gr['value']=gr['method'].vals.get(name=gr_value)
				except:
					print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  type(gr['Grade']))
					print(gr['method'])
					for gv in gr['method'].vals.all():
						print(type(gv.name),gv.name)
					print()
					print()
					raise
				if isinstance(gr['EAP Grade'],float):
					gr['EAPgrade']=gradeValue.objects.get(name=str(gr['EAP Grade'])[0])
				elif gr['Qualification Name']=='Combined Science' and str(gr['EAP Grade']).isnumeric():
					gr['EAPgrade']=gradeValue.objects.get(name=str(gr['EAP Grade'])[0])
				else:
					gr['EAPgrade']=gradeValue.objects.get(name=gr['EAP Grade'])
				baseline_grade=gr['Compare Grade']
				if isinstance(baseline_grade,float):
					baseline_grade=str(int(baseline_grade))
				try:
					gr['progress']=gr['value'].progress_value - gr['method'].vals.get(name=baseline_grade).progress_value
				except:
					raise
				if "(Multiple)" in gr['Class']:
					gr['staff']=['-']
					gr['Class']=gr['Class']+"-"+gr['subject'].name
					multiple_classes.append(gr['upn'].forename + " "+ gr['upn'].surname+","+gr['subject'].name)
				if len(gr['staff'])>1:
					staff_string=" ".join(gr['staff'])
				else:
					staff_string=gr['staff'][0]
				gr['classgroup'],classgroup_created=classgroup.objects.get_or_create(class_code=gr['Class'],defaults={'cohort':form.cleaned_data.get('cohort'),'staff':staff_string,'subject':[gr['subject']]})
				if classgroup_created:
					created_classes.append(gr['Class'])
				new_grades_df.loc[ii]=gr
				ii+=1
			new_grades_df.drop(['Qualification Name','Basket','Class','Type','Att8 Points','staff','Compare Grade','Grade','EAP Grade'],axis=1,inplace=True)
			
			print("<"+str(datetime.datetime.now()).split('.')[0]+">: Processing " + str(len(grades_df)) + " imports...")
			for i,gr in new_grades_df.iterrows():
				created_grade=grade(**gr.to_dict())
				created_grade.save()
			if len(failed_upns)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "Importing failed on following Students:")
				for u in failed_upns:
					print(student.objects.get(upn=u))
			if len(failed_grades)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "Importing failed on following grades:")
				for gr in failed_grades:
					print('Grade ' + str(gr['Grade']) + ' for ' + student.objects.get(upn=gr['upn']).__str__() + ' in ' + gr['Qualification Name'])
			if len(created_classes)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "The following classes were created:")
				for c in created_classes:
					print(c)
			if len(created_subjects)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "The following subjects were created:")
				for s in created_subjects:
					print(s)
			if len(multiple_classes)>0:
				print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "The following students had multiple classes for a subject:")
				for m in multiple_classes:
					print(m)
			students_table=students_df.to_html
			grades_table=new_grades_df.to_html
			context={'students':students_table,'grades':grades_table}
			return render(request,'analysis/quickDisplayDF.html',context)
	context={'form':form}
	return render(request,'analysis/importPrompt.html',context)
# def interrogate(request):
	# print(dir(views))
	# return views.InterrogationRoom.as_view(template_name="analysis/interrogator.html")(request)
	