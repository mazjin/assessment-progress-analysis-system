#! python3
#sisraTools.py - various scripts to automate retrieval of data processed by SISRA
import sys,getopt,getpass
from selenium import webdriver
from selenium.webdriver.support.ui import Select as wbdsel
import time,datetime,pandas as pd
import numpy as np

def logIntoSISRA(uname,pword,browser):
	"""given a username, password and webdriver object, navigates webdriver
	through SISRA log in process"""
	print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+ \
		"Creating browser instance...")
	browser.get('https://sisraanalytics.co.uk')
	print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
		"Logging in with provided details...")
	try:
		unameBox=browser.find_element_by_id('LogIn_UserName')
		unameBox.send_keys(uname)
		pwordBox=browser.find_element_by_id('LogIn_Password')
		pwordBox.send_keys(pword)
		pwordBox.submit()
	except:
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  "ERR")
		browser.close()
	time.sleep(0.5)
	try:
		browser.find_element_by_css_selector('.green').click()
	except:
		pass
	time.sleep(1)


def openStudentReports(browser,year,dd,dd_option=None):
	"""navigates browser webdriver to individual student SISRA reports for given
	data drop and year"""
	print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
		"Opening student reports area...")
	#navigate to reports from home screen, if error then quit
	try:
		browser.find_element_by_css_selector('a span img[alt="Reports"]')\
			.click()
	except:
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+  ":(")
		time.sleep(5)
		sys.exit(2)
	time.sleep(0.5)

	#open EAP area if not already open, else do nothing
	try:
		browser.find_element_by_link_text('KS 3/4').click()
	except:
		pass
	time.sleep(0.5)


	# check & select year group tab based on variables
	try:
		#loops through available yeargroups to find correct one
		yeartabs=browser.find_element_by_css_selector('.yearTabs')\
			.find_elements_by_css_selector('.year a')
		for yeartab in yeartabs:
			if ('Yr ' + year) in yeartab.text:
				yeartab.click()
				break
		time.sleep(0.5)
		#loop through available year data to find correct collection
		try:
			collection_year=dd.split(" ")[0].replace("Y","")
		except:
			collection_year=year
		if not collection_year.isnumeric():
			collection_year=year
		try:
			coll_selected=browser.find_element_by_css_selector(\
				".eapYear.open .eapYearTitle")
		except:
			coll_selected=browser.find_element_by_css_selector(\
				".eapYear .eapYearTitle")
		if collection_year not in coll_selected.text:
			coll_spans=browser.find_elements_by_css_selector(".eapYear\
			.eapYearTitle")
			for collection in coll_spans:
				if collection_year in collection.text:
						collection.click()
		else:
			coll_selected.click()
		#loop through datadrops available to find relevant one
		ddboxes=browser.find_elements_by_css_selector(".eapPub")
		for ddbox in ddboxes:
			if dd in ddbox.text:
				ddbox.click()
				break
		time.sleep(0.5)
		student_button=browser.find_element_by_css_selector(".eapPub.active")\
			.find_element_by_link_text("Students")
		student_button.click()
	except:
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
			"something else went wrong?")
		raise
	time.sleep(0.5)

	if dd_option:
		option_button=browser.find_element_by_css_selector(".vtp .avail.HasSBP")
		option_button.click()
		time.sleep(0.5)


	#open relevant comparison dataset
	comparison_dd="Baseline"
	comp_select=browser.find_element_by_css_selector(
		".dsListTitle.comp + .datasetList")
	comp_select.click()
	time.sleep(0.5)
	comp_dds=browser.find_element_by_css_selector(".dsListTitle.comp ~ div")\
		.find_elements_by_css_selector("ul>li")
	for comp_dd in comp_dds:
		if comparison_dd in comp_dd.text:
			comp_dd.click()
			break
	found_comp=browser.find_element_by_css_selector(".flyOut .dsIcon.canView")
	found_comp.click()
	time.sleep(0.5)

	#open student details area of reports
	stu_det_button=browser.find_element_by_css_selector("[data-name='Student Detail']")
	stu_det_button.click()
	time.sleep(0.5)
	stu_det_options=browser.find_elements_by_css_selector(".area.selected .rptBtn span")
	for opt in stu_det_options:
		if "Headlines" in opt.text:
			opt.click()
			break
	time.sleep(0.5)
	open_stu_det_button=browser.find_element_by_css_selector(".rptBtn.selected")\
		.find_element_by_xpath(
		"preceding-sibling::div[1][contains(@class,'lvls')]")
	open_stu_det_button.click()
	time.sleep(1.0)

def getStudentData(browser,year,dd, dd_opt=None):
	"""loops through all students in a year, retrieves student and grade data
	and returns dataframe"""
	comparison_dd="Baseline"
	if dd_opt:
		dd_name=dd+" Proj"
		dd_label="SBP from "+dd
	else:
		dd_name=dd
		dd_label=dd
	#getting dictionary of student names & upns to value in dropdown selector
	studentList=browser.find_element_by_css_selector('#ReportOptions_Stu_ID')\
		.find_elements_by_css_selector('*')
	"""while the dropdown element referened above is reused in the loop below,
	not registering it as an object, as it needs reinitialising every loop"""
	studentDict={}
	for stu in studentList:
		if stu.text!="":
			studentDict[stu.get_attribute('value')]=stu.text

	#initialising dataframes to be returned
	student_df=pd.DataFrame(columns=['upn','forename','surname','gender','reg','guest',
		'banding','pp','eal','fsm_ever','lac','sen','homestatus','attendance',
		'ks2_reading','ks2_maths','ks2_average','focus_groups'])
	grades_df=pd.DataFrame(columns=['upn','Qualification Name','Basket',
		'Class','Type','Grade''Att8 Points','EAP Grade','staff',
		'Compare Grade','progress'])
	headlines_df=pd.DataFrame(columns=['upn','datadrop','progress8',
		'attainment8', 'en_att8','ma_att8','eb_att8','op_att8','eb_filled',
		'op_filled','ebacc_entered','ebacc_achieved_std','ebacc_achieved_stg','basics_9to4','basics_9to5','att8_progress'])
	temp_counter=0
	#loop through student pages
	student_position=1
	student_number=len(studentDict)
	student_milestone=int(student_number/15)
	if student_milestone<2:
		student_milestone=1
	headline_position=0
	for key in studentDict.keys():
		if student_position % student_milestone==1:
			print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
				"Retrieving " + str(student_position) + " of " +\
				str(student_number) + " students...")
		#get upn, forename,surname from text in dropdown
		student_namestring=studentDict[key]
		split_namestring=student_namestring.split(" ")
		upn=split_namestring[-1]
		guest=(split_namestring[-3]=="(Guest)")
		if guest:
			split_namestring=split_namestring[:-3]
		else:
			split_namestring=split_namestring[:-2]
		name_break=split_namestring.index(";")
		surname=" ".join(split_namestring[:name_break])
		forename=" ".join(split_namestring[name_break+1:])

		wbdsel(browser.find_element_by_css_selector('#ReportOptions_Stu_ID'))\
			.select_by_value(str(key))
		#get vulnerable grouping info from table on profile
		filterTable=pd.read_html(browser.find_element_by_css_selector("#page.closed").get_attribute('innerHTML'))[0]
		"""rearrange info from dataframe as series - table is irregularly
		organised so must be reconstructed"""
		vgFilters=pd.Series()
		for c in range(1,len(filterTable.columns),2):
			for r in range(0,len(filterTable.index)):
				if filterTable.iloc[r,c-1] == "Focus Group":
					if "Focus Groups" not in vgFilters.index:
						vgFilters['Focus Groups']=[filterTable.iloc[r,c]]
					else:
						vgFilters["Focus Groups"].append(filterTable.iloc[r,c])
				else:
					vgFilters[filterTable.iloc[r,c-1]]=filterTable.iloc[r,c]

		if 'Focus Groups' not in vgFilters:
			vgFilters['Focus Groups']=[]
		#get KS2 and basics data table, clean up column names and indexing
		ks2Table=pd.read_html(browser\
			.find_element_by_css_selector("#page.closed")\
			.get_attribute('innerHTML'),header=0)[4]
		if "KS2" not in ks2Table.columns: #for pupils with no grades,skip
			continue
		ks2Table.columns.str.replace("\n","")
		ks2Table.columns.str.replace("%","")
		ks2Table.columns.str.strip()
		ks2Table['Dataset']=ks2Table['Dataset'].str.split(" ").str[-1]
		ks2Table.set_index(keys='Dataset',drop=True,inplace=True)
		#construct series to be entered as a row in the student dataframe
		studentEntry=pd.Series({'upn':upn,'forename':forename,'surname':surname,
			'gender':vgFilters['Gender'],
			'reg':vgFilters['Reg Group'],
			'guest':guest,
			'banding':vgFilters['Banding'],
			'pp':vgFilters['PP'],
			'eal':vgFilters['EAL'],
			'fsm_ever':vgFilters['FSM Ever'],
			'lac':vgFilters['Looked After'],
			'sen':vgFilters['SEN'],
			'homestatus':vgFilters['Home Status'],
			'attendance':vgFilters['Attendance'],
			'ks2_reading':ks2Table['KS2'].loc['English'],
			'ks2_maths':ks2Table['KS2'].loc['Maths'],
			'ks2_average':avg_ks2(re=ks2Table['KS2'].loc['English'],
				ma=ks2Table['KS2'].loc['Maths']),
			'focus_groups':vgFilters['Focus Groups']
			})
		student_df.loc[upn]=studentEntry

		#get grades table from page, clean columns and add to grades dataframe
		gradesTable=pd.read_html(browser\
			.find_element_by_css_selector("#page.closed")
			.get_attribute('innerHTML'),header=0)[3]
		gradesTable.columns=gradesTable.columns.str.replace("\n","")
		gradesTable.columns=gradesTable.columns.str.replace("%","")
		gradesTable.columns=gradesTable.columns.str.strip()
		gradesTable['upn']=upn
		del gradesTable['Eligibility']
		del gradesTable['Results Date']
		grades_df=grades_df.append(gradesTable)

		student_position+=1

		a8p8Table=pd.read_html(browser\
			.find_element_by_css_selector('#page.closed')
			.get_attribute('innerHTML'),header=0,index_col=0)[2]
		basicsTable=pd.read_html(browser\
			.find_element_by_css_selector('#page.closed')
			.get_attribute('innerHTML'),header=0,index_col=0)[4]
		ebaccTable=pd.read_html(browser\
			.find_element_by_css_selector('#page.closed')
			.get_attribute('innerHTML'),header=0,index_col=0)[5]
		a8p8Table.columns.str.strip()
		a8p8Table.index.str.strip()
		basicsTable.columns.str.strip()
		basicsTable.index.str.strip()
		ebaccTable.columns.str.strip()
		ebaccTable.index.str.strip()
		hd_entry=pd.Series({'upn':upn,'datadrop':dd_name,
			'progress8':a8p8Table.loc[dd_label+" Progress 8","Overall"],
			'attainment8':a8p8Table.loc[dd_label+" Attainment 8","Overall"],
			'en_att8':a8p8Table.loc[dd_label+" Attainment 8","English"],
			'ma_att8':a8p8Table.loc[dd_label+" Attainment 8","Maths"],
			'eb_att8':a8p8Table.loc[dd_label+" Attainment 8","EBacc"],
			'op_att8':a8p8Table.loc[dd_label+" Attainment 8","Open"],
			'eb_filled':a8p8Table.loc[dd_label+" Slots Filled","EBacc"],
			'op_filled':a8p8Table.loc[dd_label+" Slots Filled","Open"],
			'ebacc_entered':ebaccTable.loc[dd_label+" Entered","Overall"],
			'ebacc_achieved_std':ebaccTable.loc[dd_label+" Achieving (Standard)",
				"Overall"],
			'ebacc_achieved_stg':ebaccTable.loc[dd_label+" Achieving (Strong)",
				"Overall"],
			'basics_9to4':basicsTable.loc[dd_label+" - Overall","Passed 9-4"],
			'basics_9to5':basicsTable.loc[dd_label+" - Overall","Passed 9-5"],
			'att8_progress':a8p8Table.loc[comparison_dd+" Attainment 8 >",
				"Overall"]})
		headlines_df.loc[dd_name+"-"+upn]=hd_entry
	#clean and parse grades dataframe
	grades_df['staff']=grades_df['Class'].str.split().str[1:]
	grades_df['Class']=grades_df['Class'].str.split().str[0]


	for colname in ['ebacc_entered','ebacc_achieved_std','ebacc_achieved_stg',
	'basics_9to4','basics_9to5']:
		headlines_df[colname]=headlines_df[colname]=="Y"
	headlines_df['att8_progress']=headlines_df['attainment8']-\
		headlines_df['att8_progress']
	return student_df,grades_df,headlines_df

def avg_ks2(**ks2_levels):
	eff_ks2=[]
	for area,level in ks2_levels.items():
		try:
			num=float(level)
		except:
			num=np.nan
		if not np.isnan(num):
			eff_ks2.append(num)
	try:
		avg=sum(eff_ks2)/len(eff_ks2)
		return round(avg,1)
	except:
		return np.nan
