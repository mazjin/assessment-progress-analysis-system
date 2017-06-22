from django.shortcuts import render
from .models import *
from .sisraTools import *
from selenium import webdriver
from .forms import importForm
from django.http import HttpResponseRedirect
from assessment import settings
import sqlite3
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
		print(request.POST)
		if form.is_valid():
			username=form.cleaned_data.get('username')
			pw=form.cleaned_data.get('pw')
			cohort=form.cleaned_data.get('cohort').current_year
			dd_name=form.cleaned_data.get('dd_name').name
			print(username,pw,cohort,dd_name)
			browser=webdriver.Chrome()
			logIntoSISRA(username,pw,browser)
			openStudentReports(browser,cohort,dd_name)
			students_df,grades_df=getStudentData(browser,cohort,dd_name)
			students_df['cohort']=form.cleaned_data.get('cohort')

			
			browser.close()
			failed_upns=[]
			failed_grades=[]
			created_classes=[]
			for u,stu in students_df.iterrows():
				try:
					if stu['banding']=="Lower":
						band="L"
					elif stu['banding']=="Upper/High":
						band="H"
					elif stu['banding']=="Middle":
						band="M"
					else:
						band="N"
					created_student=student(upn=u,forename=stu['forename'],
						surname=stu['surname'],
						reg=classgroup.objects.get(pk="CLS"+stu['reg'].strip()),
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
			print(grades_df['Qualification Name'])
			ii=0
			for i, gr in grades_df.iterrows():
				print(type(gr))
				gr['subject']=subject.objects.get(name=gr['Qualification Name'],cohort=form.cleaned_data.get('cohort'))
				gr['method']=gr['subject'].method
				gr['value']=gr['method'].values.get(name=gr['Grade'])
				if isinstance(gr['EAP Grade'],float):
					gr['EAPgrade']=gradeValue.objects.get(name=str(gr['EAP Grade'])[0])
				elif gr['Qualification Name']=='Combined Science' and str(gr['EAP Grade']).isnumeric():
					gr['EAPgrade']=gradeValue.objects.get(name=str(gr['EAP Grade'])[0])
				else:
					gr['EAPgrade']=gradeValue.objects.get(name=gr['EAP Grade'])
				#gr['EAPgrade']=gr['method'].values.get(name=str(int(str(gr['EAP Grade'])[0])))
				gr['progress']=gr['value'].progress_value - gr['method'].values.get(name=gr['Compare Grade']).progress_value
				if len(gr['staff'])>1:
					staff_string=" ".join(gr['staff'])
				else:
					staff_string=gr['staff'][0]
				gr['classgroup'],classgroup_created=classgroup.objects.get_or_create(class_code=gr['Class'],defaults={'cohort':form.cleaned_data.get('cohort'),'staff':staff_string,'subject':[gr['subject']]})
				if classgroup_created:
					created_classes.append(gr['Class'])
				gr['datadrop']=form.cleaned_data.get('dd_name')
				gr['upn']=student.objects.get(upn=gr['upn'])
				new_grades_df.loc[ii]=gr
				ii+=1
			new_grades_df.drop(['Qualification Name','Basket','Class','Type','Att8 Points','staff','Compare Grade','Grade','EAP Grade'],axis=1,inplace=True)
			#new_grades_df.rename(columns={'EAP Grade':'EAPgrade','Grade':'value'},inplace=True)
			print(new_grades_df)
			
			for i,gr in new_grades_df.iterrows():
				created_grade=grade(**gr.to_dict())
				created_grade.save()
			if len(failed_upns)>0:
				print("Importing failed on following Students:")
				for u in failed_upns:
					print(student.objects.get(upn=u))
			if len(failed_grades)>0:
				print("Importing failed on following grades:")
				for gr in failed_grades:
					print('Grade ' + str(gr['Grade']) + ' for ' + student.objects.get(upn=gr['upn']).__str__() + ' in ' + gr['Qualification Name'])
			if len(created_classes)>0:
				print("The following classes were created:")
				for c in created_classes:
					print(c)
			students_table=students_df.to_html
			grades_table=new_grades_df.to_html
			context={'students':students_table,'grades':grades_table}
			return render(request,'analysis/quickDisplayDF.html',context)
	context={'form':form}
	return render(request,'analysis/importPrompt.html',context)
# def interrogate(request):
	# print(dir(views))
	# return views.InterrogationRoom.as_view(template_name="analysis/interrogator.html")(request)
	