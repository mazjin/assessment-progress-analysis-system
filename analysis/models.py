from django.db import models
import pandas as pd
from django.apps import apps
import numpy as np
from numbers import Number
# Create your models here.
avg_headline_measures=["en_att8","ma_att8","eb_att8","op_att8",
	'attainment8','progress8','att8_progress',"eb_filled","op_filled",]
pct_headline_measures=["ebacc_achieved_std","ebacc_achieved_stg",
	"ebacc_entered","basics_9to4","basics_9to5"]

def get_measure_obj(measure):
	"""returns the model object corresponding to a measure"""
	measure=measure.split("__")[0]
	for m in [grade,headline]:
		for f in m._meta.get_fields():
			if f.name==measure:
				return m
	raise KeyError('measure not found in models')

def avg_measure(measure,obj,Qfilter=None,**filters):
    """finds the average value of the measure of a type of object for given
    filters. E.G. for the average progress per grade in Maths Y11, the measure
    is "progress", the object type is the grade, and the filters are the Maths
    subject and Y11 cohort"""

    if not Qfilter is None:
        found_objs=obj.objects.filter(Qfilter,**filters)
    else:
        found_objs=obj.objects.filter(**filters)
    avg=found_objs.aggregate(models.Avg(measure))[measure+'__avg']
    if avg is None:
        return np.nan
    else:
        return round(avg,3)

def pct_measure(measure,comparison,obj,only_exceeding=False,Qfilter=None,
    **filters):
    """finds the percentage of a set of objects that meet or exceed (or only
    exceed, if the flag is set) a given value for comparison, for the given
    filters."""

    if not isinstance(comparison,bool)and not isinstance(comparison,Number):
        filters[comparison+'__isnull']=False
    if not Qfilter is None:
        found_objs=obj.objects.filter(Qfilter,**filters)
    else:
        found_objs=obj.objects.filter(**filters)
    num_total=found_objs.count()

    if only_exceeding:
        filter_string=measure+'__gt'
    else:
        filter_string=measure+'__gte'
    if not isinstance(comparison,bool)and not isinstance(comparison,Number):
        comparison=models.F(comparison)
    num_counted=found_objs.filter(**{filter_string:comparison}).count()
    if num_total==0:
        return np.nan
    else:
        return round((num_counted/num_total)*100,1)

def residual_measure(measure, obj,Qfilter=None, **filters):
    """finds the residual of a set of objects, within given filters.
    Value returned is the average of the residuals for each student"""
    if not Qfilter is None:
        objs_found=obj.objects.filter(Qfilter,**filters)
    else:
        objs_found=obj.objects.filter(**filters)
    if objs_found.count()<=0:
        return np.nan
    stus_found=[]
    residuals=pd.Series()
    for o in objs_found:
        stu=o.upn
        temp_filters=dict(filters)
        for t in filters.keys():
            if "classgroup" in t or "subject" in t:
                temp_filters.pop(t)
        stu_set=obj.objects.filter(upn=stu, **temp_filters)
        if not Qfilter is None:
            stu_set=found_objs.filter(Qfilter)
        stu_avg=stu_set.aggregate(models.Avg(measure))[measure+'__avg']
        try:
            if stu not in stus_found:
                stus_found.append(stu)
                stu_objs=objs_found.filter(upn=stu)
                if stu_objs.count()>1:
                    stu_val=stu_objs.aggregate(models.Avg(measure))[measure+'__avg']
                    objs_found=objs_found.exclude(upn=stu)
                elif "__" in measure:
                    obj_fks=measure.split("__")
                    stu_val=o
                    for fk in obj_fks:
                        stu_val=getattr(stu_val,fk)
                else:
                    stu_val=getattr(o,measure)
                stu_val=float(stu_val)
                residual=stu_val-stu_avg
        except:
            print("Error calculating " + str(stu_val) + " - " + str(stu_avg))
            residual=np.nan
        residuals[stu.upn]=residual
    residual_avg=residuals.mean()
    if residual_avg is None:
        return np.nan
    else:
        return round(residual_avg,2)

def get_Qfilters(grp_type, values):
    filters=None
    if isinstance(values,list):
        for val in values:
            if filters is None:
                filters=models.Q(**{grp_type:val})
            else:
                filters=filters|models.Q(**{grp_type:val})
    elif values is None or values=="*" or values=="":
        filters=None
    else:
        filters=models.Q(**{grp_type:values})
    return filters

def gap_measure(calc_function,grp_type,grpA_values,grpB_values,**options):
    """finds the gap between two calculated avg/pct/residual measures for groups
     A and B, specified by given filters"""

    grpA_filters=get_Qfilters(grp_type,grpA_values)
    grpB_filters=get_Qfilters(grp_type,grpB_values)

    grpA_measure=calc_function(Qfilter=grpA_filters,**options)
    grpB_measure=calc_function(Qfilter=grpB_filters,**options)
    try:
        gap=grpA_measure-grpB_measure
    except:
        gap=np.nan
    return gap

def series_measure(function,group_filters,**options):
	"""return a series of measure calculations for given groups and filters"""
	results=pd.Series()
	for group_key, group_filter in group_filters.items():
		joined_options={**options,**group_filter}
		results[group_key]=function(**joined_options)
	return results

def df_measure(function,row_filters,col_filters,**options):
	"""return a dataframe of measure calculations for given row and column
	filters"""
	results=pd.DataFrame()
	for col_key,col_filter in col_filters.items():
		joined_options={**options,**col_filter}
		results[col_key]=series_measure(function,row_filters,**joined_options)
	return results

def count_measure(obj,Qfilter=None,**filters):
	"""returns the number of objects found with given filters"""
	if not Qfilter is None:
		found_objs=obj.objects.filter(Qfilter,**filters)
	else:
		found_objs=obj.objects.filter(**filters)
	count=found_objs.count()
	if count is None:
		return np.nan
	else:
		return count

def avg_grade_filter_points(df,measure=None):
	new_df=pd.DataFrame(index=df.index)
	if measure==None:
		if "#" in df:
			new_df['#']=df['#']
		for column in df:
			new_column=column.replace("Score","Grade")
			if "Attainment" in column and "+=-" in column and \
			not "Residual" in column:
				new_df[new_column]=df[column].apply(lambda x: round((x-3)/9,2))
			elif "Attainment" in column:
				new_df[new_column]=df[column]
			elif "Progress" in column or ("Attainment" in column and \
			"+=-" in column and "Residual" in column):
				new_df[new_column]=df[column].apply(lambda x: round(x/9,2))
		return new_df
	elif measure=="progress":
		def func(x):
			return round((x-3)/9,3)
	elif measure=="value__progress_value":
		def func(x):
			return round(x/9,3)
	else:
		def func(x):
			return x
	for column in df:
		if column=="#":
			new_df['#']=df['#']
		else:
			new_df[column]=df[column].apply(func)
	return new_df

def clean_filters(dicti):
	for fld in ['subject','classgroup','subject__name','classgroup__class_code',
	'subject__cohort']:
		if fld in dicti:
			dicti['upn__grade__'+fld]=dicti.pop(fld)
	return dicti


def get_default_filters_dict(class_of_filters,measure,**filters):
	"""defines a row or column query as a dictionary of filter conditions, to be
	used in functions of the studentGrouping class"""
	if "datadrop__in" in filters:
		filters.pop("datadrop__in")
	if class_of_filters=="short_student":
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
			'All Lower':{'upn__wide_banding':"L"},
			'All Middle':{'upn__wide_banding':"M"},
			'All Higher':{'upn__wide_banding':"H"},
			'No Band':{'upn__wide_banding':"N"}
			}
	elif class_of_filters=="student":
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
			'Lower Extreme':{'upn__narrow_banding':"Lx"},
			'Lower':{'upn__narrow_banding':"L"},
			'Middle':{'upn__narrow_banding':"M"},
			'Middle (Lower)':{'upn__narrow_banding':"Ml"},
			'Middle (Higher)':{'upn__narrow_banding':"Mh"},
			'Higher':{'upn__narrow_banding':"H"},
			'Higher Extreme':{'upn__narrow_banding':"Hx"},
			'No Band':{'upn__wide_banding':"N"},
			'Low Boys':{'upn__wide_banding':"L",'upn__gender':"M"},
			'Middle Boys':{'upn__wide_banding':"M",'upn__gender':"M"},
			'High Boys':{'upn__wide_banding':"H",'upn__gender':"M"},
			'Low Girls':{'upn__wide_banding':"L",'upn__gender':"F"},
			'Middle Girls':{'upn__wide_banding':"M",'upn__gender':"F"},
			'High Girls':{'upn__wide_banding':"H",'upn__gender':"F"},
			'High Girls':{'upn__wide_banding':"H",'upn__gender':"F"},
			'Low PP Boys':{'upn__wide_banding':"L",'upn__gender':"M",'upn__pp':True},
			'Middle PP Boys':{'upn__wide_banding':"M",'upn__gender':"M",'upn__pp':True},
			'High PP Boys':{'upn__wide_banding':"H",'upn__gender':"M",'upn__pp':True},
			'Low PP Girls':{'upn__wide_banding':"L",'upn__gender':"F",'upn__pp':True},
			'Middle PP Girls':{'upn__wide_banding':"M",'upn__gender':"F",'upn__pp':True},
			'High PP Girls':{'upn__wide_banding':"H",'upn__gender':"F",'upn__pp':True},
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
			'All Lower':{'upn__wide_banding':'L'},
			'Lower Extreme':{'upn__narrow_banding':'Lx'},
			'Lower':{'upn__narrow_banding':'L'},
			'All Middle':{'upn__wide_banding':'M'},
			'Middle (Lower)':{'upn__narrow_banding':'Ml'},
			'Middle (Higher)':{'upn__narrow_banding':'Mh'},
			'All Higher':{'upn__wide_banding':'H'},
			'Higher':{'upn__narrow_banding':'H'},
			'Higher Extreme':{'upn__narrow_banding':'Hx'},
			'No Banding':{'upn__wide_banding':'N'},
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
			dict=clean_filters(dict)
	return returnDict

class studentGrouping(models.Model):
	"""provides set of common functions for child classes yeargroup, classgroup,
	datadrop and subject"""
	class Meta:
		abstract = True


class subjectTag(models.Model):
	"""A tag to identify similar subjects across yeargroups"""
	name=models.CharField(max_length=100,help_text="The string identifying the \
	tag")

	def __str__(self):
		return self.name

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
		return self.name + "(P"+str(self.progress_value) +", A"+str(self.att8_value)+")"

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

	name=models.CharField(max_length=100,help_text="The subject's name, as \
	timetabled.")
	method=models.ForeignKey(gradeMethod,
		help_text="The grade method used by the subject.")
	attainment8bucket=models.CharField(max_length=2,choices=buckets,
		help_text="The highest Attainment 8 bucket the subject can be counted \
		in.")
	cohort=models.ForeignKey(yeargroup,
		help_text="The yeargroup studying the subject.")

	faculty=models.CharField(max_length=100,
		help_text="The faculty the subject is part of.",null=True,blank=True)

	"""defines whether a subject is optional or core, and whether it counts for
	English Baccalaureate"""
	option_subject=models.BooleanField(default=True)
	ebacc_subject=models.BooleanField(default=False)

	tags=models.ManyToManyField(subjectTag,help_text="Set of tags linking \
	subject to other subjects across yeargroups")

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
		return len(grade.objects.filter(subject=self).distinct()\
			.values_list('upn'))

class classgroup(studentGrouping):
	"""A timetabled class or registration group."""
	class_code=models.CharField(max_length=10,
		help_text="The class group's unique identifier code.")
	cohort=models.ForeignKey(yeargroup,
		help_text="The yeargroup that the class group's students belong to.")
	staff=models.CharField(max_length=12,
		help_text="The staff member(s) assigned to this group.")
	subject=models.ManyToManyField(subject,
		help_text="The subject(s) studied by the group.",blank=True)

	def __str__(self):
		return self.class_code + "(Y"+self.cohort.current_year+")"

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
	upn=models.CharField(max_length=13,primary_key=True,
		help_text="Unique 13-character identifier used in many school systems.")
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

	wide_bands=(
	("H","Upper/High Ability"),
	("M","Middle Ability"),
	("L","Lower Ability"),
	("N","No data"))

	narrow_bands=(
	("Hx","Extremely High Ability"),
	("H","Upper/High Ability"),
	("Mh","Middle Ability, Higher division"),
	("M","Middle Ability"),
	("Ml","Middle Ability, Lower division"),
	("L","Lower Ability"),
	("Lx","Extremely Low Ability"),
	("N","No data"))

	wide_banding=models.CharField(max_length=1,choices=wide_bands,
	 help_text="The wider ability grouping the student belongs to.",default="N")
	narrow_banding=models.CharField(max_length=2,choices=narrow_bands,
	 help_text="The finer ability grouping the student belongs to.",default="N")

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

	guest_status=models.BooleanField(help_text="Whether the student is a guest \
	pupil at the school", default=False)

	home_types=(
		("N","N/A"),
		("T","Traveller"),
	)
	home_status=models.CharField(help_text="The home grouping the student\
	 belongs to", max_length=1,default="N",choices=home_types)

	attendance_bands=(
		("PA","Persistent Absence"),
		("AC","Attendance Concern"),
		("EA","Expected Attendance"),
		("FA","Full Attendance"),
	)
	attendance=models.CharField(help_text="The level of attendance the \
	student has attained so far this school year",max_length=2,default="EA",
	choices=attendance_bands)


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
		null=True)
	baseline_grade=models.ForeignKey(gradeValue,help_text="The grade attained \
	by the student in baseline testing.",null=True,blank=True,related_name="BL")
	EAPgrade=models.ForeignKey(gradeValue,
		help_text="The estimated attainment for the student in this data drop.",
		related_name="EAP",null=True,blank=True)
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
		help_text="Whether the student achieved the EBacc (standard grade) or \
		not.")
	ebacc_achieved_stg=models.BooleanField(default=False,
		help_text="Whether the student achieved the EBacc (strong grade) or \
		not.")

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
