from analysis.models import *

s=subject.objects.get(name="Maths",cohort__current_year="9")

class_queryset=list(s.classgroup_set.all().order_by('class_code'))
student_filters_dict={'All':{},
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
filters={'subject':s,'datadrop__name':"Y9 DD3",'datadrop__cohort__current_year':"9"}

class_dict={}
for cl in class_queryset:
	class_dict[cl.class_code]={'classgroup':cl}


class_queryset.append(s)
class_dict[s.name]={}