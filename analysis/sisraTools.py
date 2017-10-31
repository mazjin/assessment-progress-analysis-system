#! python3
#sisraTools.py - various scripts to automate retrieval of data processed by SISRA
import sys,getopt,getpass
from selenium import webdriver
from selenium.webdriver.support.ui import Select as wbdsel
import time,datetime,pandas as pd


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
		pwordBox=browser.find_element_by_id('LogIn_Password')
		unameBox.send_keys(uname)
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
	time.sleep(0.5)

def setMegDD(year):
	"""used to identify MEG targets for a given year group"""
		#decide & select relevant target data set for comparison
	if year in '1109':
		meg_dd='KS4'
	elif year in '78':
		meg_dd='KS3'
	return meg_dd

def openDDReport(browser,year, dd):
	"""navigates browser webdriver to the correct SISRA report for populating
	the SLT overview table"""
	#navigate to reports from home screen, if error then quit
	print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
		"Opening filter reports...")
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

		selectedDD=browser.find_element_by_css_selector(
			'.eapPub.active .eapInfo .line')
		time.sleep(0.5)
		if dd not in selectedDD.text and dd!=selectedDD.text:
			ddList=browser.find_elements_by_css_selector(
				'.eapPub .eapInfo .line')
			for ddbox in ddList:
				if dd in ddbox.text or dd==ddbox.text:
					ddbox.click()
	except:
		raise
	time.sleep(0.5)

	#open relevant data drop dataset
	try:
		browser.find_element_by_css_selector(
			'.eapPub.active .EAPRptBtn .button').click()
	except:
		print ("can't find report button")
	time.sleep(.5)

	#identify meg name,use it to select comparison dataset
	meg_dd=setMegDD(str(year).strip())
	try:
		compareSelect=browser.find_element_by_id('compareSelect')
		compareOpts=compareSelect.find_elements_by_css_selector('*')
		for opt in compareOpts:
			if meg_dd.lower() in opt.text.lower():
				opt.click()
				break

	except:
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
			"couldn't select megs!")
		raise
	time.sleep(0.5)

	#select correct report type
	navButtons=browser.find_elements_by_css_selector('#reportNavWrapper .rept')
	navGrids=browser.find_elements_by_css_selector(
		'#reportNavWrapper .list-grid')
	if len(navButtons)!=len(navGrids):
		print ('more grids than buttons, exiting')
		sys.exit(2)

	for i in range(len(navButtons)):
		#print(navButtons[i].text)
		if "grades" in navButtons[i].text.lower():
			gradesButton=navButtons[i]
			gradesGrid=navGrids[i]
			break
	gradesButton.click()
	#click correct button in gradesGrid
	time.sleep(0.5)
	repTypes=gradesGrid.find_elements_by_css_selector('.title-y')
	for reptype in repTypes:
		if "totals" in reptype.text.lower():
			filtersRow=reptype.find_element_by_xpath('..')

	filtersButtons=filtersRow.find_elements_by_link_text('Go!')
	filtersButtons[0].click()
	time.sleep(1.0)

def sltOverview(browser,year,dd):
	"""generates table populated with percentage of each student group
	(boys, girls, disadvantaged, EAL,etc.) meeting and exceeding MEG targets for
	each subject"""
	print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
		"Collecting performance data for subjects...")
	meg_dd=setMegDD(str(year).strip())
	"""set report for correct values, get dictionaries of subjects and students
	and their selection values"""
	repQualBox=browser.find_element_by_id('ReportOptions_Qual_ID')
	subjOptions=repQualBox.find_elements_by_css_selector('*')
	subjDict={}
	for subop in subjOptions:
		if subop.text!="":
			subjDict[subop.get_attribute('value')]=subop.text
	browser.find_element_by_css_selector('.percentage').click()
	resultsDict={}
	#loop through subjects in dropdown menu
	for key in subjDict.keys():
		#select subject in dropdown
		subj=subjDict[key]
		print (str(subj) + "," + str(key))
		wbdsel(browser.find_element_by_id('ReportOptions_Qual_ID'))\
			.select_by_value(str(key))
		time.sleep(.5)

		#read table into pandas DataFrame
		subject_df=pd.read_html(browser.find_element_by_tag_name('html')\
			.get_attribute('innerHTML'),header=0,index_col=1)[8]

		"""clean strings in column and index names - need to rewrite this to use
			pandas object.str accessor!"""
		newnames=[]
		newcols=[]
		for n in subject_df.columns:
			n=str(n)
			n=n.replace("\n","")
			n=n.replace("%","")
			n=n.strip()
			newcols.append(n)
		subject_df.columns=newcols
		for n in subject_df['Name']:
			n=n.replace("\n","")
			n=n.replace("%","")
			n=n.strip()
			newnames.append(n)
		subject_df['Name']=newnames

		"""discard entries in dataframe containing irrelevant comparison data,
		attach subject name to index names, add to results dictionary"""
		subject_df=subject_df[subject_df['Name'] != 'Difference >']
		subject_df=subject_df[subject_df['Name'] != meg_dd+ ' MEGs >']
		subject_df.index=subject_df['Name'] + "_" + subject_df.index
		resultsDict[subj]=subject_df.iloc[:,11:15]

	#populate new dataframe with collated results
	results_df=pd.DataFrame()
	for sub in resultsDict.keys():
		results_df[sub+' >=']=resultsDict[sub]['>= '+meg_dd+' MEGs']
		results_df[sub+' >']=resultsDict[sub]['> '+meg_dd+' MEGs']
	results_df.fillna('N/A',inplace=True) #replaces "NaN" values
	#output to file, return collated dataframe
	results_df.to_csv(dd + '.csv')
	print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
		'Done! Results collated and output to ' + dd + '.csv')
	return results_df

def main():
	"""takes username, password, selected webdriver method, datadrop name and
	relevant yeargroup and returns/exports an SLT overview table """

	helpMessage="Usage: sisraTools -u/--user <username> -p/-pass <password> \
	-b/--browser <browser> -y/--year <cohort year> -d/--datadrop \
	<data drop name>"

	try:
		opts,args=getopt.getopt(sys.argv[1:],'u:p:b:y:d:dd:',
			['user=','username=','pass=','password=','browser=','year=',
			'dataset=','datadrop=','dd='])
	except getopt.GetoptError:
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+helpMessage)
		sys.exit(2)

	uname=""
	pword=""
	brwsr=''
	year=""
	dd=""

	for opt,arg in opts:
		if opt in ('-u','--username','--user'):
			uname=arg
		elif opt in ('-p','--pass','--password'):
			pword=arg
		elif opt in ('-b','--browser'):
			brwsr=arg
		elif opt in ('-d','--dataset','--datadrop','--dd','-dd'):
			dd=arg
		elif opt in ('-y','--year'):
			year=arg

	if uname=="":
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
			'Please enter your SISRA username.')
		uname=input()

	if year=="":
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
			"Please enter the current year group for the cohort, e.g. if \
			accessing info for the current Year 8, enter 8.")
		year=input()

	if dd=="":
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+\
			"Please enter the name of the data drop to access, e.g. Y7 DD3, \
			Y11 DD2, PPEs, Exams")
		dd=input()

	if pword=="":
		pword=getpass.getpass('Please enter your SISRA password.\n')

	if brwsr=='' or brwsr.lower()=='chrome':
		browser=webdriver.Chrome()
	elif brwsr.lower()=='ff' or brwsr.lower()=='firefox':
		browser=webdriver.Firefox()
	else:
		print("<"+str(datetime.datetime.now()).split('.')[0]+">: "+helpMessage)
		sys.exit(2)


	logIntoSISRA(uname,pword,browser)
	openDDReport(browser,year,dd)
	sltOverview(browser,year,dd)
	return df
if __name__=="__main__":main()

def openStudentReports(browser,year,dd):
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
	found_dd=browser.find_element_by_css_selector(".flyOut .cdsItemBtn")
	found_dd.click()
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

def getStudentData(browser,year,dd):
	"""loops through all students in a year, retrieves student and grade data
	and returns dataframe"""
	comparison_dd="Baseline"
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
	student_df=pd.DataFrame(columns=['upn','forename','surname','gender','reg',
		'banding','pp','eal','fsm_ever','lac','sen','homestatus','attendance',
		'ks2_reading','ks2_maths'])
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
		#print(student_namestring)
		split_namestring=student_namestring.split(" ")
		upn=split_namestring[0]
		if split_namestring[-1]=="(Guest)":
			forename=split_namestring[-2]
			surname=" ".join(split_namestring[2:-2])
		else:
			forename=split_namestring[-1]
			surname=" ".join(split_namestring[2:-1])
		#go to relevant student profile
		wbdsel(browser.find_element_by_css_selector('#ReportOptions_Stu_ID'))\
			.select_by_value(str(key))
		#get vulnerable grouping info from table on profile
		filterTable=pd.read_html(browser.find_element_by_css_selector("#page.closed").get_attribute('innerHTML'))[0]
		"""rearrange info from dataframe as series - table is irregularly
		organised so must be reconstructed"""
		vgFilters=pd.Series()
		for c in range(1,8,2):
			for r in range(0,3):
				vgFilters[filterTable.iloc[r,c-1]]=filterTable.iloc[r,c]

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
			'banding':vgFilters['Banding'],
			'pp':vgFilters['PP'],
			'eal':vgFilters['EAL'],
			'fsm_ever':vgFilters['FSM Ever'],
			'lac':vgFilters['Looked After'],
			'sen':vgFilters['SEN'],
			'homestatus':vgFilters['Home Status'],
			'attendance':vgFilters['Attendance'],
			'ks2_reading':ks2Table['KS2'].loc['English'],
			'ks2_maths':ks2Table['KS2'].loc['Maths']})
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
		hd_entry=pd.Series({'upn':upn,'datadrop':dd,
			'progress8':a8p8Table.loc[dd+" Progress 8","Overall"],
			'attainment8':a8p8Table.loc[dd+" Attainment 8","Overall"],
			'en_att8':a8p8Table.loc[dd+" Attainment 8","English"],
			'ma_att8':a8p8Table.loc[dd+" Attainment 8","Maths"],
			'eb_att8':a8p8Table.loc[dd+" Attainment 8","EBacc"],
			'op_att8':a8p8Table.loc[dd+" Attainment 8","Open"],
			'eb_filled':a8p8Table.loc[dd+" Slots Filled","EBacc"],
			'op_filled':a8p8Table.loc[dd+" Slots Filled","Open"],
			'ebacc_entered':ebaccTable.loc[dd+" Entered","Overall"],
			'ebacc_achieved_std':ebaccTable.loc[dd+" Achieving (Standard)",
				"Overall"],
			'ebacc_achieved_stg':ebaccTable.loc[dd+" Achieving (Strong)",
				"Overall"],
			'basics_9to4':basicsTable.loc[dd+" - Overall","Passed 9-4"],
			'basics_9to5':basicsTable.loc[dd+" - Overall","Passed 9-5"],
			'att8_progress':a8p8Table.loc[comparison_dd+" Attainment 8 >",
				"Overall"]})
		headlines_df.loc[dd+"-"+upn]=hd_entry
	#clean and parse grades dataframe
	grades_df['staff']=grades_df['Class'].str.split().str[1:]
	grades_df['Class']=grades_df['Class'].str.split().str[0]
	# grades_df['Grade'].fillna("X",inplace=True)
	# grades_df['EAP Grade'].fillna("X",inplace=True)
	# grades_df['Compare Grade'].fillna("X",inplace=True)

	#may reimplement these, but remove for now
	del student_df['attendance']
	del student_df['homestatus']

	#calculate average ks2 for students
	student_df['ks2_average']=round((student_df['ks2_maths']+\
		student_df['ks2_reading'])*10/2.0)/10.0
		#dividing & multiplying by 10s needed to get decimal values from round
	for colname in ['ebacc_entered','ebacc_achieved_std','ebacc_achieved_stg',
	'basics_9to4','basics_9to5']:
		headlines_df[colname]=headlines_df[colname]=="Y"
	headlines_df['att8_progress']=headlines_df['attainment8']-\
		headlines_df['att8_progress']
	return student_df,grades_df,headlines_df
