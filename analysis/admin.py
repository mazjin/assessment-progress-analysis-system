from django.contrib import admin

# Register your models here.
from analysis.models import gradeValue,gradeMethod,yeargroup,datadrop,subject,\
classgroup,student,grade,headline,subjectTag,focusGroup

admin.site.register(gradeValue)
admin.site.register(gradeMethod)
admin.site.register(yeargroup)
admin.site.register(datadrop)
admin.site.register(subject)
admin.site.register(classgroup)
admin.site.register(student)
admin.site.register(grade)
admin.site.register(headline)
admin.site.register(subjectTag)
admin.site.register(focusGroup)
