from analysis.views import *
import pdb

cc="10a/Ma1"
s="Maths"
dd="Y10 DD3"

cols=["progress","attainment","headline","all"]

for sub_row in ["student","classgroup","yeargroup","datadrop"]:
	for col in cols:
		try:
			print(get_standard_table("subject",sub_row,col,10,name=s))
			print("subject, " + sub_row + ", " + col)
		except:
			print("Error on subject," + sub_row + "," + col)
		
		pdb.set_trace()

for class_row in ["student","subject","yeargroup","datadrop"]:
	for col in cols:
		try:
			print(get_standard_table("classgroup",class_row,col,10,class_code=cc))
			print("class, " + class_row + ", " + col)
		except:
			print("Error on classgroup," + class_row + "," + col)
		
		pdb.set_trace()
for dd_row in ["student","classgroup","yeargroup"]:
	for col in cols:
		try:
			print(get_standard_table("datadrop",dd_row,col,10,name=dd))
			print("dd, " + dd_row + ", " + col)
		except:
			print("Error on datadrop," + dd_row + "," + col)
		
		pdb.set_trace()
