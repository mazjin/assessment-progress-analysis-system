from django.db import models

# Create your models here.
class gradeValue(models.Model):
	"""A definition of a grade for use in a grade method (NOT an instance of a grade, see  grade class instead)"""
	name=models.CharField(max_length=5, help_text="The grade symbol, e.g. A+, 9=, 4.3, Pass")
	progress_value=models.IntegerField("The value of the grade in the school's internal progress system.")
	att8_value=models.DecimalField(decimal_places=1,max_digits=4, help_text="The value of the grade towards Attainment 8.",blank=True)
	
	def __str__(self):
		return self.name
		
	
class gradeMethod(models.Model):
	"""the grading method associated with a subject group"""
	text=models.CharField(
	max_length=100,
	help_text="The identifying label for the grading scheme.")
	
	vals=models.ManyToManyField(gradeValue,related_name="gradeset",help_text="The set of grades used/included in the grading method.")
	
	pass_grade=models.ForeignKey(gradeValue,help_text="The grade considered a pass or strong pass for the purposes of headline measures (e.g. EnMa Basics, Ebacc).")
	
	def __str__(self):
		return self.text
	
class yeargroup(models.Model):
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
	cohort=models.CharField(max_length=9,choices=cohort_choices,primary_key=True,help_text="The graduating year of this yeargroup.")
	current_year_choices=(
	("7","Year 7"),
	("8","Year 8"),
	("9","Year 9"),
	("10","Year 10"),
	("11","Year 11"),
	)
	current_year=models.CharField(max_length=2,choices=current_year_choices,help_text="The current yeargroup the cohort is in.")
	
	def __str__(self):
		return self.cohort + " (current Year " + self.current_year +")"
		
	def reggroups(self):
		return self.classgroup_set.filter(subject=None)
	
class datadrop(models.Model):
	"""A scheduled collection of data; an individual dataset"""
	name=models.CharField(max_length=30,help_text="The label identifying the datadrop, e.g. Y9 DD3")
	date=models.DateField(help_text="The date the datadrop ended.")
	cohort=models.ForeignKey(yeargroup, help_text="The yeargroup the data drop belongs to.")
	
	def __str__(self):
		return self.name
	
class subject(models.Model):
	"""A subject studied by students in a yeargroup"""
	buckets=(
	("en","English"),
	("ma","Maths"),
	("eb","Ebacc"),
	("op","Open")
	)
	
	name=models.CharField(max_length=100,help_text="The subject's name.")
	method=models.ForeignKey(gradeMethod,help_text="The grade method used by the subject.")
	attainment8bucket=models.CharField(max_length=2,choices=buckets,help_text="The highest Attainment 8 bucket the subject can be counted in.")
	cohort=models.ForeignKey(yeargroup,help_text="The yeargroup studying the subject.")
	
	def avg_progress(self,band="",dd="",pp=""):
		"""returns average progress score for selected band and datadrop - defaults to all bands and most recent datadrop for linked cohort"""
		if dd=="":
			dd=datadrop.objects.all().filter(cohort=self.cohort).order_by('-date')[0]
		elif isinstance(dd,str):	
			dd=datadrop.objects.get(name=dd,cohort=self.cohort)
		filters={'datadrop':dd}
		if isinstance(pp,bool):
			filters['upn__pp']=pp
		filters['upn__banding__contains']=band
		progress_avg_set=self.grade_set.filter(**filters)
		progress_avg=progress_avg_set.aggregate(models.Avg('progress'))['progress__avg']
		if not progress_avg is None:
			return round(progress_avg,2)
		else:
			return "-"
	def staff_list(self):
		staff_tuple_list=list(self.classgroup_set.all().values_list('staff'))
		staff_list=[]
		for st in staff_tuple_list:
			staff_list.append(st[0])
		return staff_list
	def __str__(self):
		return self.name + " (Y" + self.cohort.current_year+")"
	
	def num_classes(self,dd=""):
		if dd=="":
			dd=datadrop.objects.all().filter(cohort=self.cohort).order_by('-date')[0]
		elif isinstance(dd,str):	
			dd=datadrop.objects.get(name=dd,cohort=self.cohort)
		return self.classgroup_set.all().count()
		
	def num_students(self,dd=""):
		if dd=="":
			dd=datadrop.objects.all().filter(cohort=self.cohort).order_by('-date')[0]
		elif isinstance(dd,str):	
			dd=datadrop.objects.get(name=dd,cohort=self.cohort)
		return len(set(grade.objects.filter(subject=self).values_list('upn')))
	
	def avg_progress_higher(self,dd=""):
		"""calls avg_progress for higher banding for templating"""
		return self.avg_progress(band="H",dd=dd)

	def avg_progress_middle(self,dd=""):
		"""calls avg_progress for middle banding for templating"""
		return self.avg_progress(band="M",dd=dd)

	def avg_progress_lower(self,dd=""):
		"""calls avg_progress for lower banding for templating"""
		return self.avg_progress(band="L",dd=dd)	
	
class classgroup(models.Model):
	"""The timetabled class or registration group."""
	class_code=models.CharField(max_length=10,primary_key=True,help_text="The unique class identifier code.")
	cohort=models.ForeignKey(yeargroup, help_text="The yeargroup that the class group's students belong to.")
	staff=models.CharField(max_length=12, help_text="The staff member(s) assigned to this group.")
	subject=models.ManyToManyField(subject,help_text="The subject(s) studied by the group.",blank=True)
	
	def __str__(self):
		return self.class_code
		
	@property
	def class_size(self):
		"""returns integer number of pupils in the class"""
		if self.subject.count()==0:
			return student.objects.all().filter(reg=self).count()
		else:
			return len(set(gr.upn for gr in self.grade_set.all()))
	
	@property
	def students(self):
		"""returns set of unique student records with a grade attached to the classgroup"""
		return set(gr.upn for gr in self.grade_set.all())
		
	def avg_progress(self,band="",dd="",pp="",subj=""):
		"""returns average progress score for selected band and datadrop - defaults to all bands and most recent datadrop for linked cohort"""
		if dd=="":
			dd=datadrop.objects.all().filter(cohort=self.cohort).order_by('-date')[0]
		elif isinstance(dd,str):	
			dd=datadrop.objects.get(name=dd,cohort=self.cohort)
		filters={'datadrop':dd}
		if subj!="":
			filters['subject']=subject.objects.get(name=subj,cohort=dd.cohort)
		if isinstance(pp,bool):
			filters['upn__pp']=pp
		filters['upn__banding__contains']=band
		progress_avg_set=self.grade_set.filter(**filters)
		progress_avg=progress_avg_set.aggregate(models.Avg('progress'))['progress__avg']
		if not progress_avg is None:
			return round(progress_avg,2)
		else:
			return "-"
	
	def avg_progress_pp(self):
		return self.avg_progress(pp=True)
		
	def avg_progress_npp(self):
		return self.avg_progress(pp=False)
	
	def avg_progress_pp_gap(self):
		return round(self.avg_progress_pp()-self.avg_progress_npp(),2)
		
	def avg_progress_higher(self,dd=""):
		"""calls avg_progress for higher banding for templating"""
		return self.avg_progress(band="H",dd=dd)

	def avg_progress_middle(self,dd=""):
		"""calls avg_progress for middle banding for templating"""
		return self.avg_progress(band="M",dd=dd)

	def avg_progress_lower(self,dd=""):
		"""calls avg_progress for lower banding for templating"""
		return self.avg_progress(band="L",dd=dd)		

	def avg_progress_residual_subject(self,subj=None):
		if subj is None:
			subj=self.subject.all()[0]
		return round(self.avg_progress() - subj.avg_progress(),2)
	
class student(models.Model):
	"""A pupil at the school"""
	upn=models.CharField(max_length=13,primary_key=True,help_text="Unique 13-character identifier used in many school systems.")
	forename=models.CharField(max_length=50,help_text="The student's forename(s).")
	surname=models.CharField(max_length=75,help_text="The student's surname(s).")
	reg=models.ForeignKey(classgroup,related_name="reg_group",help_text="The registration group the pupil belongs to.")
	genders=(
	("M","Male"),
	("F","Female"),
	("N","Not Specified")
	)
	gender=models.CharField(max_length=1,choices=genders,help_text="The gender identity of the student.")
	
	cohort=models.ForeignKey(yeargroup, help_text="The yeargroup the student belongs to.")
	
	ks2_reading=models.CharField(max_length=5,help_text="The student's reading score at the end of KS2.")
	ks2_maths=models.CharField(max_length=5, help_text="The student's maths score at the end of KS2.")
	ks2_average=models.CharField(max_length=5, help_text= "The student's average reading and maths score at the end of KS2")
	
	bands=(
	("H","Upper/High Ability"),
	("M","Middle Ability"),
	("L","Lower Ability"),
	("N","No data"))
	banding=models.CharField(max_length=1,choices=bands, help_text="The ability grouping the student belongs to.")
	
	eal=models.BooleanField(help_text="Whether the student has a native language other than English.")
	pp=models.BooleanField(help_text="Whether the student is a pupil premium student.")
	
	sen_types=(
	("N","Non SEN"),
	("K","K SEN"),
	("E","EHCP"))
	sen=models.CharField(max_length=1,choices=sen_types, help_text="The Special Educational Need code applicable to the student.", default="N")
	
	lac=models.BooleanField(help_text="Whether the student is a Looked After Child (in social care." )
	fsm_ever=models.BooleanField(help_text="Whether the student has ever been eligible for Free School Meals.")
	
	#class_codes=models.ManyToManyField(classgroup, help_text="The classes that the student belongs to.",blank=True)
	
	def __str__(self):
		return self.forename+ " " + self.surname + " ("+self.upn+")"
	
class grade(models.Model):
	"""An instance of a grade assigned to a student in a subject as part of a data drop."""
	value=models.ForeignKey(gradeValue,help_text="The grade given.")
	method=models.ForeignKey(gradeMethod,help_text="The grade method the grade belongs to.")
	upn=models.ForeignKey(student, help_text="The UPN of the student the grade has been given to.")
	datadrop=models.ForeignKey(datadrop, help_text="The data drop that the grade is part of.")
	subject=models.ForeignKey(subject, help_text="The subject the grade was given in.")
	progress=models.IntegerField(blank=True, help_text="The progress the student has made from their baseline.",default=0)
	EAPgrade=models.ForeignKey(gradeValue,help_text="The estimated attainment for the student in this data drop.",related_name="EAP")
	classgroup=models.ForeignKey(classgroup,help_text="The class the grade was given in",null=True)
	def __str__(self):
		return self.datadrop.name+"/"+self.upn.__str__()+"/"+self.subject.__str__()+"/"+self.value.name