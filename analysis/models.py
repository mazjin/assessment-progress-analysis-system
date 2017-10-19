from django.db import models
import pandas
from django.apps import apps
import numpy as np
# Create your models here.
avg_headline_measures=["en_att8","ma_att8","eb_att8","op_att8",
	'attainment8','progress8','att8_progress',"eb_filled","op_filled",]
pct_headline_measures=["ebacc_achieved_std","ebacc_achieved_stg",
	"ebacc_entered","basics_9to4","basics_9to5"]

def clean_filters(dict,measure):
	for innerkey,val in dict.copy().items():
		if innerkey[0:9]=="yeargroup":
			dict[innerkey.replace("yeargroup","datadrop__cohort")]=val
			dict.pop(innerkey,None)
		if (innerkey[0:7]=="subject" or innerkey[0:10]=="classgroup") and\
		(measure in avg_headline_measures or measure in \
		pct_headline_measures):
			dict['upn__grade__'+innerkey]=val
			dict['upn__grade__datadrop']=models.F('datadrop')
			dict.pop(innerkey,None)
		# if  innerkey[0:10]=="class_code":
			# dict['upn__grade__classgroup__class_code']=val
			# dict.pop(innerkey,None)

	return dict


def get_default_filters_dict(class_of_filters,measure,**filters):
	"""defines a row or column query as a dictionary of filter conditions, to be
	used in functions of the studentGrouping class"""
	if "datadrop__in" in filters:
		filters.pop("datadrop__in")
	if class_of_filters=="student":
		returnDict= {'All':{},
			'Male':{'upn__gender':"M"},
			'Female':{'upn__gender':"F"},
			'PP':{'upn__pp':True},
			'NPP':{'upn__pp':False},
			'EAL':{'upn__eal':True},
			'LAC':{'upn__lac':True},
			'FSM Ever':{'upn__fsm_ever':True},
			'NSEN':{'upn__sen':"N"},
			'KSEN':{'upn__sen':"K"},
			'EHCP':{'upn__sen':"E"},
			'Lower':{'upn__banding':"L"},
			'Middle':{'upn__banding':"M"},
			'Higher':{'upn__banding':"H"},
			'No Band':{'upn__banding':"N"}
			}
	elif class_of_filters=="extended_student":
		returnDict= {'All':{},
			'Male':{'upn__gender':"M"},
			'Female':{'upn__gender':"F"},
			'PP':{'upn__pp':True},
			'NPP':{'upn__pp':False},
			'EAL':{'upn__eal':True},
			'LAC':{'upn__lac':True},
			'FSM Ever':{'upn__fsm_ever':True},
			'NSEN':{'upn__sen':"N"},
			'KSEN':{'upn__sen':"K"},
			'EHCP':{'upn__sen':"E"},
			'Lower':{'upn__banding':"L"},
			'Middle':{'upn__banding':"M"},
			'Higher':{'upn__banding':"H"},
			'No Band':{'upn__banding':"N"},
			'Low Boys':{'upn__banding':"L",'upn__gender':"M"},
			'Middle Boys':{'upn__banding':"M",'upn__gender':"M"},
			'High Boys':{'upn__banding':"H",'upn__gender':"M"},
			'Low Girls':{'upn__banding':"L",'upn__gender':"F"},
			'Middle Girls':{'upn__banding':"M",'upn__gender':"F"},
			'High Girls':{'upn__banding':"H",'upn__gender':"F"},
			'Low PP Boys':{'upn__banding':"L",'upn__gender':"M",'upn__pp':True},
			'Middle PP Boys':{'upn__banding':"M",'upn__gender':"M",'upn__pp':True},
			'High PP Boys':{'upn__banding':"H",'upn__gender':"M",'upn__pp':True},
			'Low PP Girls':{'upn__banding':"L",'upn__gender':"F",'upn__pp':True},
			'Middle PP Girls':{'upn__banding':"M",'upn__gender':"F",'upn__pp':True},
			'High PP Girls':{'upn__banding':"H",'upn__gender':"F",'upn__pp':True},
			}
	elif class_of_filters=="att8bucket":
		returnDict= {'All':{},
			'Maths':{'subject__attainment8bucket':'ma'},
			'English':{'subject__attainment8bucket':'en'},
			'EBacc':{'subject__attainment8bucket':'eb'},
			'Open':{'subject__attainment8bucket':'op'},
			}
	elif class_of_filters=="banding":
		returnDict= {'All':{},
			'Lower':{'upn__banding':'L'},
			'Middle':{'upn__banding':'M'},
			'Upper/High':{'upn__banding':'H'},
			'No Banding':{'upn__banding':'N'},
			}
	elif class_of_filters=="subject_blocks":
		returnDict= {'All':{},
			'Core':{'subject__option_subject':False},
			'Option':{'subject__option_subject':True},
			'EBacc':{'subject__ebacc_subject':True},
			'Non-EBacc':{'subject__ebacc_subject':False},
			}
	else:
		"""if not a fixed set of filters, populate from objects in db based on
		class, code specific to each class removes invalid filters and replaces
		them with valid ones where possible"""
		if class_of_filters=="classgroup" :
			filters.pop('datadrop',None)
			filters.pop('datadrop__name',None)
			if "classgroup" in filters:
				filters['class_code']=filters['classgroup'].class_code
				filters.pop('classgroup',None)

		elif class_of_filters=="subject" or class_of_filters=="faculty":
			if "subject" in filters:
				filters['name']=filters['subject'].name
				filters.pop('subject',None)
			elif "subject__name" in filters:
				filters['name']=filters['subject__name']
				filters.pop('subject__name',None)
			filters.pop('datadrop',None)
			filters.pop('datadrop__name',None)

		elif class_of_filters=="datadrop":
			if 	"datadrop__name" in filters:
				filters['name']=filters['datadrop__name']
				filters.pop('datadrop__name',None)
			if "datadrop" in filters:
				filters['id']=filters['datadrop'].id
				filters.pop('datadrop',None)
			if "subject" in filters or "faculty" in filters:
				filters['cohort__in']=yeargroup.objects.filter(
					subject=filters['subject'])
				filters.pop('subject',None)
			elif "subject__name" in filters:
				filters['cohort__in']=yeargroup.objects.filter(
					subject__name__contains=filters['subject__name'])
				filters.pop('subject__name',None)
			if "classgroup" in filters:
				filters['cohort']=filters['classgroup'].cohort
				filters.pop('classgroup',None)

		elif class_of_filters=="yeargroup" :
			if "subject__name" in filters and measure=="progress":
				filters['subject__in']=subject.objects.filter(
					name__contains=filters['subject__name'])
				filters.pop('subject__name',None)
			if "cohort" in filters and measure=="progress":
				filters['cohort']=filters['cohort'].cohort
			filters.pop('subject',None)

		#get queryset or set of objects from db based on filters
		if class_of_filters in ['yeargroup','datadrop','subject',
		'classgroup']:
			qset=apps.get_model('analysis',class_of_filters).\
				objects.filter(**filters)
		elif class_of_filters=="faculty":
			qset=['Maths','English','Science','Humanities','MFL',
				'Arts','Technology','IT',None]
			for sub in subject.objects.filter(**filters):
				if sub.faculty not in qset:
					qset.add(sub.faculty)

		#sorting set for each class
		if class_of_filters=="yeargroup":
			class_of_filters="subject__cohort"
			qset=qset.order_by('cohort')
		elif class_of_filters=="datadrop":
			qset=qset.order_by('cohort','-date')
		elif class_of_filters=="subject":
			qset=qset.order_by('name','faculty')
		elif class_of_filters=="classgroup":
			qset=qset.order_by('class_code')
		elif class_of_filters=="faculty":
			class_of_filters="subject__faculty"
		#populate returning dictionary with set/queryset
		returnDict={}
		if len(qset)>=2:
			returnDict['All']={}
		if class_of_filters=="subject":
			for q in qset:
				returnDict[q.name]={'subject__name':q.name}
		else:
			for q in qset:
				if q is None and "faculty" in class_of_filters:
					returnDict["Other"]={class_of_filters:q}
				else:
					returnDict[q.__str__()]={class_of_filters:q}
	if measure in avg_headline_measures or measure in pct_headline_measures:
		for outerkey,dict in returnDict.items():
			dict=clean_filters(dict,measure)
	return returnDict

class studentGrouping(models.Model):
	"""provides set of common functions for child classes yeargroup, classgroup,
	datadrop and subject"""
	class Meta:
		abstract = True

	def avg_progress_df_filters_col(self,col_filters_dict,
		row_filters_dict,**filters):
		"""returns a dataframe of the average progress for a combination of
		group filters - rows and columns both defined by dicts of dicts"""
		results=pandas.DataFrame()
		for col_name,col_filter in col_filters_dict.items():
			joined_filters_col={**filters,**col_filter}
			results[col_name]=self.avg_progress_series(row_filters_dict,
				joined_filters_col)
		return results.reindex(index=row_filters_dict.keys(),
			columns=col_filters_dict.keys())

	def avg_progress_series(self,group_filters_dict,filters):
		"""returns the average progress of a set of group filters given by a
		dict of dicts"""
		results={}
		for group_key,group_filter in group_filters_dict.items():
			joined_filters={**group_filter,**filters}
			results[group_key]=self.avg_progress(**joined_filters)
		return pandas.Series(results)

	def get_grades(self,**filters):
		"""returns queryset of grades according to filters entered"""
		grades_found=grade.objects.filter(**filters)
		return grades_found

	def avg_progress(self,**filters):
		"""returns average progress score of set of grades defined by filters"""
		progress_avg=self.get_grades(**filters).aggregate(
			models.Avg('progress'))['progress__avg']
		if not progress_avg is None:
			return round(progress_avg,2)
		else:
			return np.nan

	def avg_progress_template(self,**filters):
		"""returns average progress for "default values without having to set
		filters directly - used for directly embedding values in page
		templates"""
		filters['datadrop']=datadrop.objects.all().filter(cohort=self.cohort)\
			.order_by('-date')[0]
		filters[self.__class__.__name__]=self
		return self.avg_progress(**filters)

	def avg_progress_pp(self,**filters):
		"""calculates average progress for pupil premium students"""
		filters['upn__pp']=True
		return self.avg_progress_template(**filters)

	def avg_progress_npp(self,**filters):
		"""calculates average progress for non-pupil premium students"""
		filters['upn__pp']=False
		return self.avg_progress_template(**filters)

	def avg_progress_pp_gap(self,**filters):
		"""calculates the gap in average progress between pupil premium and
		non-PP students"""
		return round(self.avg_progress_pp()-self.avg_progress_npp(),2)

	def avg_progress_higher(self,**filters):
		"""calls avg_progress for higher banding for templating"""
		filters['upn__banding__contains']="H"
		return self.avg_progress_template(**filters)

	def avg_progress_middle(self,**filters):
		"""calls avg_progress for middle banding for templating"""
		filters['upn__banding__contains']="M"
		return self.avg_progress_template(**filters)

	def avg_progress_lower(self,**filters):
		"""calls avg_progress for lower banding for templating"""
		filters['upn__banding__contains']="L"
		return self.avg_progress_template(**filters)

	def avg_headline(self,measure,**filters):
		stu_filters={}
		headlines_found=headline.objects.filter(**filters).distinct()
		hd_avg=headlines_found.aggregate(models.Avg(measure))[measure+'__avg']
		if not hd_avg is None:
			return round(hd_avg,4)
		else:
			return np.nan

	def avg_headline_df(self, col_filters_dict,row_filters_dict,filters,
		measure):
		results=pandas.DataFrame()
		for col_name,col_filter in col_filters_dict.items():
			joined_filters_col={**filters,**col_filter}
			results[col_name]=self.avg_headline_series(row_filters_dict,
				joined_filters_col,measure)
		return results.reindex(index=row_filters_dict.keys(),
			columns=col_filters_dict.keys())
		return results

	def avg_headline_series(self,group_filters_dict,filters,measure):
		results={}
		for group_key,group_filter in group_filters_dict.items():
			joined_filters={**group_filter,**filters}
			results[group_key]=self.avg_headline(measure,**joined_filters)
		return pandas.Series(results)

	def pct_EAP(self,only_exceeding=False,**filters):
		filtered_grades=self.get_grades(EAPgrade__progress_value__gt=0,**filters)
		num_total=filtered_grades.count()
		if only_exceeding:
			num_meeting=filtered_grades.filter(value__progress_value__gt=models.F('EAPgrade__progress_value')).count()
		else:
			num_meeting=filtered_grades.filter(value__progress_value__gte=models.F('EAPgrade__progress_value')).count()
		if num_total==0:
			return np.nan
		else:
			return round((num_meeting/num_total)*100,1)

	def pct_EAP_series(self,only_exceeding,group_filters_dict,filters):
		results={}
		for group_key,group_filter in group_filters_dict.items():
			joined_filters={**group_filter,**filters}
			results[group_key]=self.pct_EAP(only_exceeding,**joined_filters)
		return pandas.Series(results)

	def pct_EAP_df(self,only_exceeding,col_filters_dict,row_filters_dict,filters):
		results=pandas.DataFrame()
		for col_name,col_filter in col_filters_dict.items():
			joined_filters_col={**filters,**col_filter}
			results[col_name]=self.pct_EAP_series(only_exceeding,
				row_filters_dict,joined_filters_col)
		return results.reindex(index=row_filters_dict.keys(),
			columns=col_filters_dict.keys())
		return results

	def pct_headline(self,measure,**filters):
		filtered_headlines=headline.objects.filter(**{measure+"__isnull":False},**filters)
		num_total=filtered_headlines.count()
		num_meeting=filtered_headlines.filter(**{measure:True}).count()
		if num_total==0:
			return np.nan
		else:
			return round((num_meeting/num_total)*100,1)

	def pct_headline_df(self, col_filters_dict,row_filters_dict,filters,
		measure):
		results=pandas.DataFrame()
		for col_name,col_filter in col_filters_dict.items():
			joined_filters_col={**filters,**col_filter}
			results[col_name]=self.pct_headline_series(row_filters_dict,
				joined_filters_col,measure)
		return results.reindex(index=row_filters_dict.keys(),
			columns=col_filters_dict.keys())
		return results

	def pct_headline_series(self,group_filters_dict,filters,measure):
		results={}
		for group_key,group_filter in group_filters_dict.items():
			joined_filters={**group_filter,**filters}
			results[group_key]=self.pct_headline(measure,**joined_filters)
		return pandas.Series(results)


class gradeValue(models.Model):
	"""A definition of a grade for use in a grade method (NOT an instance of a
	grade, see  grade class instead)"""
	name=models.CharField(max_length=5, help_text="The grade symbol, e.g. A+, \
	9=, 4.3, Pass")
	progress_value=models.IntegerField("The value of the grade in the school's \
	internal progress system.")
	att8_value=models.DecimalField(decimal_places=1,max_digits=4,
		help_text="The value of the grade towards Attainment 8.",blank=True)

	def __str__(self):
		return self.name

class gradeMethod(models.Model):
	"""the grading method associated with a subject group"""
	text=models.CharField(
	max_length=100,
	help_text="The identifying label for the grading scheme.")

	vals=models.ManyToManyField(gradeValue,related_name="gradeset",
		help_text="The set of grades used/included in the grading method.")

	pass_grade=models.ForeignKey(gradeValue,help_text="The grade considered a \
		pass or strong pass for the purposes of headline measures (e.g. EnMa \
		Basics, Ebacc).")

	def __str__(self):
		return self.text

class yeargroup(studentGrouping):
	"""A cohort of students"""
	cohort_choices=(
		("2017-2018","2017-2018"),
		("2018-2019","2018-2019"),
		("2019-2020","2019-2020"),
		("2020-2021","2020-2021"),
		("2021-2022","2021-2022"),
		("2022-2023","2022-2023"),
		("2023-2024","2023-2024"),
		("2024-2025","2024-2025"),
		("2025-2026","2025-2026"),
		("2026-2027","2026-2027"),
		)
	cohort=models.CharField(max_length=9,choices=cohort_choices,
		primary_key=True,help_text="The graduating year of this yeargroup.")
	current_year_choices=(
	("7","Year 7"),
	("8","Year 8"),
	("9","Year 9"),
	("10","Year 10"),
	("11","Year 11"),
	)
	current_year=models.CharField(max_length=2,choices=current_year_choices,
		help_text="The current yeargroup the cohort is in.")

	def __str__(self):
		return self.cohort + " (current Year " + self.current_year +")"

	def reggroups(self):
		return self.classgroup_set.filter(subject=None)

class datadrop(studentGrouping):
	"""A scheduled collection of data; an individual dataset"""
	name=models.CharField(max_length=30,help_text="The label identifying the \
	datadrop, e.g. Y9 DD3")
	date=models.DateField(help_text="The date the datadrop ended.")
	cohort=models.ForeignKey(yeargroup,
		help_text="The yeargroup the data drop belongs to.")

	def __str__(self):
		return self.name + " (Y"+self.cohort.current_year+")"

class subject(studentGrouping):
	"""A subject studied by students in a yeargroup"""
	buckets=(
	("en","English"),
	("ma","Maths"),
	("eb","Ebacc"),
	("op","Open")
	)

	name=models.CharField(max_length=100,help_text="The subject's name.")
	method=models.ForeignKey(gradeMethod,
		help_text="The grade method used by the subject.")
	attainment8bucket=models.CharField(max_length=2,choices=buckets,
		help_text="The highest Attainment 8 bucket the subject can be counted in.")
	cohort=models.ForeignKey(yeargroup,
		help_text="The yeargroup studying the subject.")

	faculty=models.CharField(max_length=100,
		help_text="The faculty the subject is part of.",null=True,blank=True)

	"""defines whether a subject is optional or core, and whether it counts for
	English Baccalaureate"""
	option_subject=models.BooleanField(default=True)
	ebacc_subject=models.BooleanField(default=False)

	def staff_list(self):
		"""returns set of staff codes for teachers of the subject"""
		staff_tuple_list=list(self.classgroup_set.all().values_list('staff'))
		staff_list=[]
		for st in staff_tuple_list:
			staff_list.append(st[0])
		staff_list=set(staff_list)
		return staff_list

	def __str__(self):
		return self.name + " (Y" + self.cohort.current_year+")"

	def num_classes(self,dd=""):
		"""returns number of classes in the subject - used for page templates"""
		if dd=="":
			dd=datadrop.objects.all().filter(cohort=self.cohort)\
				.order_by('-date')[0]
		elif isinstance(dd,str):
			dd=datadrop.objects.get(name=dd,cohort=self.cohort)
		return self.classgroup_set.all().count()

	def num_students(self,dd=""):
		"""returns the number of students studying the subject as of the data
		drop specified (defaults to most recent) - used for page templates"""
		if dd=="":
			dd=datadrop.objects.all().filter(cohort=self.cohort)\
				.order_by('-date')[0]
		elif isinstance(dd,str):
			dd=datadrop.objects.get(name=dd,cohort=self.cohort)
		return len(grade.objects.filter(subject=self).distinct().values_list('upn'))

class classgroup(studentGrouping):
	"""A timetabled class or registration group."""
	class_code=models.CharField(max_length=10,primary_key=True,
		help_text="The class group's unique identifier code.")
	cohort=models.ForeignKey(yeargroup,
		help_text="The yeargroup that the class group's students belong to.")
	staff=models.CharField(max_length=12,
		help_text="The staff member(s) assigned to this group.")
	subject=models.ManyToManyField(subject,
		help_text="The subject(s) studied by the group.",blank=True)

	def __str__(self):
		return self.class_code

	@property
	def class_size(self):
		"""returns integer number of pupils in the class"""
		if self.subject.count()==0:
			return student.objects.all().filter(reg=self).count()
		else:
			return self.grade_set.all().distinct().count()

	@property
	def students(self):
		"""returns set of unique student records with a grade attached to the
		classgroup"""
		return self.grade_set.all().distinct()

	def avg_progress_residual_subject(self,subj=None,**filters):
		"""returns the average progress relative to that of the whole subject
		- used for templates"""
		if subj is None:
			subj=self.subject.all()[0]
		return round(self.avg_progress(**filters) - subj.avg_progress(),2)

	def avg_progress_att8bucket(self,**filters):
		"""returns the average progress for the students in the class in
		subjects in the same attainment 8 category - used for templates"""
		filters['upn__in']=self.students
		filters['classgroup__class_code__contains']=""
		if not "subject__attainment8bucket" in filters:
			filters['subject__attainment8bucket']=self.subject.all()[0]\
				.attainment8bucket
		return self.avg_progress(**filters)

	def avg_progress_residual_att8bucket(self,**filters):
		"""returns the difference between the average progress of the class
		and that of the same pupils in subjects in the same attainment 8 bucket
		 - used for page templates"""
		try:
			return round(self.avg_progress(**filters) - \
				self.avg_progress_att8bucket(**filters),2)
		except TypeError:
			return ""

class student(models.Model):
	"""A pupil at the school"""
	upn=models.CharField(max_length=13,primary_key=True,help_text="Unique 13-character identifier used in many school systems.")
	forename=models.CharField(max_length=50,
		help_text="The student's forename(s).")
	surname=models.CharField(max_length=75,
		help_text="The student's surname(s).")
	reg=models.ForeignKey(classgroup,related_name="reg_group",
		help_text="The registration group the pupil belongs to.")
	genders=(
	("M","Male"),
	("F","Female"),
	("N","Not Specified")
	)
	gender=models.CharField(max_length=1,choices=genders,
		help_text="The gender identity of the student.")

	cohort=models.ForeignKey(yeargroup,
		help_text="The yeargroup the student belongs to.")

	ks2_reading=models.CharField(max_length=5,
		help_text="The student's reading score at the end of KS2.")
	ks2_maths=models.CharField(max_length=5,
		help_text="The student's maths score at the end of KS2.")
	ks2_average=models.CharField(max_length=5,
		help_text= "The student's average reading and maths score at the end of\
			 KS2")

	bands=(
	("H","Upper/High Ability"),
	("M","Middle Ability"),
	("L","Lower Ability"),
	("N","No data"))
	banding=models.CharField(max_length=1,choices=bands, help_text="The ability\
		 grouping the student belongs to.")

	eal=models.BooleanField(help_text="Whether the student has a native \
		language other than English.")
	pp=models.BooleanField(help_text="Whether the student is a pupil premium \
		student.")

	sen_types=(
	("N","Non SEN"),
	("K","K SEN"),
	("E","EHCP"))
	sen=models.CharField(max_length=1,choices=sen_types,
		help_text="Special Educational Need code applicable to the student.",
		default="N")

	lac=models.BooleanField(help_text="Whether the student is a Looked After \
		Child (in social care)." )
	fsm_ever=models.BooleanField(help_text="Whether the student has ever been \
		eligible for Free School Meals.")

	def __str__(self):
		return self.forename+ " " + self.surname + " ("+self.upn+")"

class grade(models.Model):
	"""An instance of a grade assigned to a student in a subject as part of a
	data drop."""
	value=models.ForeignKey(gradeValue,help_text="The grade given.")
	method=models.ForeignKey(gradeMethod,
		help_text="The grade method the grade belongs to.")
	upn=models.ForeignKey(student,
		help_text="The UPN of the student the grade has been given to.")
	datadrop=models.ForeignKey(datadrop,
		help_text="The data drop that the grade is part of.")
	subject=models.ForeignKey(subject,
		help_text="The subject the grade was given in.")
	progress=models.IntegerField(blank=True,
		help_text="The progress the student has made from their baseline.",
		default=0)
	EAPgrade=models.ForeignKey(gradeValue,
		help_text="The estimated attainment for the student in this data drop.",
		related_name="EAP")
	classgroup=models.ForeignKey(classgroup,
		help_text="The class the grade was given in",null=True)
	def __str__(self):
		return self.datadrop.name+"/"+self.upn.__str__()+"/"+\
		 self.subject.__str__()+"/"+self.value.name

class headline(models.Model):
	"""set of headline measures for each student and datadrop"""
	id=models.CharField(max_length=43, help_text="The datadrop and student \
	upn the headline measures are linked to.",primary_key=True)
	upn=models.ForeignKey(student,
		help_text="The student the headline figures pertain to.")
	datadrop=models.ForeignKey(datadrop,
		help_text="The datadrop the headline figures pertain to.")
	progress8=models.DecimalField(blank=True,null=True,
		decimal_places=2, max_digits=4,
		help_text="The PROJECTED, INACCURATE Progress 8 figure calculated \
			for the student/DD.")

	attainment8=models.DecimalField(decimal_places=1,max_digits=3,default=0,
		help_text="The Attainment8 calculated for the student/DD.")

	en_att8=models.DecimalField(decimal_places=1,max_digits=3,default=0,
		help_text="The score for the English Att8 bucket.")
	ma_att8=models.DecimalField(decimal_places=1,max_digits=3,default=0,
		help_text="The score for the Maths Att8 bucket.")
	eb_att8=models.DecimalField(decimal_places=1,max_digits=3,default=0,
		help_text="The score for the EBacc Att8 bucket.")
	op_att8=models.DecimalField(decimal_places=1,max_digits=3,default=0,
		help_text="The score for the Open Att8 bucket.")

	eb_filled=models.IntegerField(default=0,
		help_text="The number of subjects in the Ebacc Att8 bucket.")
	op_filled=models.IntegerField(default=0,
		help_text="The number of subjects in the Open Att8 bucket.")

	ebacc_entered=models.BooleanField(default=False,
		help_text="Whether the student qualified to enter the EBacc or not.")
	ebacc_achieved_std=models.BooleanField(default=False,
		help_text="Whether the student achieved the EBacc (standard grade) or not.")
	ebacc_achieved_stg=models.BooleanField(default=False,
		help_text="Whether the student achieved the EBacc (strong grade) or not.")

	basics_9to4=models.BooleanField(default=False,
		help_text="Whether the student achieved a standard pass in both \
		English and Maths")
	basics_9to5=models.BooleanField(default=False,
		help_text="Whether the student achieved a strong pass in both \
		English and Maths")
	att8_progress=models.DecimalField(decimal_places=1,max_digits=3,default=0,
		help_text="The difference in Attainment 8 score between this datadrop\
		 and baseline.")

	def __str__(self):
		return self.datadrop.name +"/"+self.upn.upn
