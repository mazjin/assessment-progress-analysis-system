#! python3
#sisraTools.py - various scripts to automate retrieval of data processed by SISRA
import sys,getopt,getpass
from selenium import webdriver
from selenium.webdriver.support.ui import Select as wbdsel
import time,pandas as pd


def logIntoSISRA(uname,pword,browser):


	browser.get('https://sisraanalytics.co.uk')

	try:
		unameBox=browser.find_element_by_id('LogIn_UserName')
		unameBox.send_keys(uname)
		pwordBox=browser.find_element_by_id('LogIn_Password')
		pwordBox.send_keys(pword)
		pwordBox.submit()
	except:
		print("ERR")
		browser.close()

	try:
		browser.find_element_by_css_selector('.green').click()
	except:
		pass
	time.sleep(0.5)
	
def setMegDD(year):
		#decide & select relevant target data set for comparison
	if year in '1109':
		meg_dd='KS4'
	elif year in '78':
		meg_dd='KS3'
	return meg_dd

def openDDReport(browser,year, dd):
	#navigate to reports from home screen, if error then quit
	try:
		browser.find_element_by_css_selector('a span img[alt="Reports"]').click()
	except:
		print(":(")
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
		yeartabs=browser.find_element_by_css_selector('.yearTabs').find_elements_by_css_selector('.year a')
		for yeartab in yeartabs:
			if ('Yr ' + year) in yeartab.text:
				yeartab.click()
				break
		
		selectedDD=browser.find_element_by_css_selector('.eapPub.active .eapInfo .line')
		time.sleep(0.5)
		if dd not in selectedDD.text and dd!=selectedDD.text:
			ddList=browser.find_elements_by_css_selector('.eapPub .eapInfo .line')
			for ddbox in ddList:
				if dd in ddbox.text or dd==ddbox.text:
					ddbox.click()
	except:
		print("something else went wrong?")
		raise
	time.sleep(0.5)

	#open relevant data drop dataset
	try:
		browser.find_element_by_css_selector('.eapPub.active .EAPRptBtn .button').click()
	except:
		print ("can't find report button")
	time.sleep(.5)

	meg_dd=setMegDD(str(year).strip())
	
	try:
		compareSelect=browser.find_element_by_id('compareSelect')
		compareOpts=compareSelect.find_elements_by_css_selector('*')
		for opt in compareOpts:
			if meg_dd.lower() in opt.text.lower():
				opt.click()
				break

	except:
		print("couldn't select megs!")
		raise
	time.sleep(0.5)

	#select correct report type
	navButtons=browser.find_elements_by_css_selector('#reportNavWrapper .rept')
	navGrids=browser.find_elements_by_css_selector('#reportNavWrapper .list-grid')

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
	meg_dd=setMegDD(str(year).strip())
	#set report for correct values
	repQualBox=browser.find_element_by_id('ReportOptions_Qual_ID')
	#qualSelect=wbdsel(repQualBox)
	subjOptions=repQualBox.find_elements_by_css_selector('*')
	subjDict={}
	for subop in subjOptions:
		#print(subop.text)
		if subop.text!="":
			subjDict[subop.get_attribute('value')]=subop.text
	browser.find_element_by_css_selector('.percentage').click()
	#print(str(subjDict))
	resultsDict={}
	for key in subjDict.keys():
		subj=subjDict[key]
		print (str(subj) + "," + str(key))
		wbdsel(browser.find_element_by_id('ReportOptions_Qual_ID')).select_by_value(str(key))
		time.sleep(.5)
		subject_df=pd.read_html(browser.find_element_by_tag_name('html').get_attribute('innerHTML'),header=0,index_col=1)[8]
		
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
		
		subject_df=subject_df[subject_df['Name'] != 'Difference >']
		subject_df=subject_df[subject_df['Name'] != meg_dd+ ' MEGs >']
		subject_df.index=subject_df['Name'] + "_" + subject_df.index
		resultsDict[subj]=subject_df.iloc[:,11:15]

	results_df=pd.DataFrame()
	for sub in resultsDict.keys():
		results_df[sub+' >=']=resultsDict[sub]['>= '+meg_dd+' MEGs']
		results_df[sub+' >']=resultsDict[sub]['> '+meg_dd+' MEGs']
	results_df.fillna('N/A',inplace=True) #replaces "NaN" values
	results_df.to_csv(dd + '.csv')
	print('Done! Results collated and output to ' + dd + '.csv')
	return results_df
	
def main():
	helpMessage="<insert help message here>"

	try:
		opts,args=getopt.getopt(sys.argv[1:],'u:p:b:y:d:dd:',['user=','username=','pass=','password=','browser=','year=','dataset=','datadrop=','dd='])
	except getopt.GetoptError:
		print(helpMessage)
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
		print('Please enter your SISRA username.')
		uname=input()
	
	if year=="":
		print("Please enter the current year group for the cohort, e.g. if accessing info for the current Year 8, enter 8.")
		year=input()
		
	if dd=="":
		print("Please enter the name of the data drop to access, e.g. Y7 DD3, Y11 DD2, PPEs, Exams")
		dd=input()
		

	if pword=="":
		pword=getpass.getpass('Please enter your SISRA password.\n')
	
	if brwsr=='' or brwsr.lower()=='chrome':
		browser=webdriver.Chrome()
	elif brwsr.lower()=='ff' or brwsr.lower()=='firefox':
		browser=webdriver.Firefox()
	else:
		print(helpMessage)
		sys.exit(2)
	
	
	logIntoSISRA(uname,pword,browser)
	openDDReport(browser,year,dd)
	sltOverview(browser,year,dd)
	return df
if __name__=="__main__":main()

def openStudentReports(browser,year,dd):
	#navigate to reports from home screen, if error then quit
	try:
		browser.find_element_by_css_selector('a span img[alt="Reports"]').click()
	except:
		print(":(")
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
		yeartabs=browser.find_element_by_css_selector('.yearTabs').find_elements_by_css_selector('.year a')
		for yeartab in yeartabs:
			if ('Yr ' + year) in yeartab.text:
				yeartab.click()
				break
		
		selectedDD=browser.find_element_by_css_selector('.eapPub.active .eapInfo .line')
		time.sleep(0.5)
		if dd not in selectedDD.text and dd!=selectedDD.text:
			ddList=browser.find_elements_by_css_selector('.eapPub .eapInfo .line')
			for ddbox in ddList:
				if dd in ddbox.text or dd==ddbox.text:
					ddbox.click()
	except:
		print("something else went wrong?")
		raise
	time.sleep(0.5)

	#open relevant data drop dataset
	try:
		browser.find_element_by_css_selector('.eapPub.active .EAPRptBtn .button').click()
	except:
		print ("Can't find report button!")
	time.sleep(.5)
	
	comparison_dd="Y9 DD1"
	
	try:
		compareSelect=browser.find_element_by_id('compareSelect')
		compareOpts=compareSelect.find_elements_by_css_selector('*')
		for opt in compareOpts:
			if comparison_dd.lower() in opt.text.lower():
				opt.click()
				break

	except:
		print("Can't find baseline dataset!")
		raise
	time.sleep(0.5)
	
	#select correct report type
	navButtons=browser.find_elements_by_css_selector('#reportNavWrapper .rept')
	navGrids=browser.find_elements_by_css_selector('#reportNavWrapper .list-grid')

	if len(navButtons)!=len(navGrids):
		print ('more grids than buttons, exiting')
		sys.exit(2)

	for i in range(len(navButtons)):
		if "student" in navButtons[i].text.lower():
			foundButton=navButtons[i]
			foundGrid=navGrids[i]
			break
	foundButton.click()
	#click correct button in gradesGrid
	time.sleep(0.5)
	repTypes=foundGrid.find_elements_by_css_selector('.title-y')
	for reptype in repTypes:
		if "headlines" in reptype.text.lower():
			filtersRow=reptype.find_element_by_xpath('..')

	filtersButtons=filtersRow.find_elements_by_link_text('Go!')
	filtersButtons[0].click()
	time.sleep(1.0)
	
def getStudentData(browser,year,dd):
	comparison_dd="Y9 DD1"
	#getting dictionary of student names & upns to value in dropdown selector
	studentList=browser.find_element_by_css_selector('#ReportOptions_Stu_ID').find_elements_by_css_selector('*') #while this element is reused in the loop below, no point registering it as an object, as it will need reinitialising every loop
	studentDict={}
	for stu in studentList:
		if stu.text!="":
			studentDict[stu.get_attribute('value')]=stu.text
	
	#initialising dataframes to be returned
	student_df=pd.DataFrame(columns=['upn','forename','surname','gender','reg','banding','pp','eal','fsm_ever','lac','sen','homestatus','attendance','ks2_reading','ks2_maths'])
	grades_df=pd.DataFrame(columns=['upn','Qualification Name','Basket','Class','Type','Grade''Att8 Points','EAP Grade','staff','Compare Grade','progress'])
	temp_counter=0
	#loop through student plages
	for key in studentDict.keys():
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
		wbdsel(browser.find_element_by_css_selector('#ReportOptions_Stu_ID')).select_by_value(str(key))
		#get vulnerable grouping info from table on profile
		filterTable=pd.read_html(browser.find_element_by_css_selector("#page.closed").get_attribute('innerHTML'))[7]
		#rearrange info from dataframe'd table to series - table is irregularly organised so must be reconstructed
		vgFilters=pd.Series()
		for c in range(1,8,2):
			for r in range(0,3):
				vgFilters[filterTable.iloc[r,c-1]]=filterTable.iloc[r,c]
		
		#get KS2 and basics data table, clean up column names and indexing
		ks2Table=pd.read_html(browser.find_element_by_css_selector("#page.closed").get_attribute('innerHTML'),header=0)[11]
		ks2Table.columns.str.replace("\n","")
		ks2Table.columns.str.replace("%","")
		ks2Table.columns.str.strip()
		ks2Table['Dataset']=ks2Table['Dataset'].str.split(" ").str[-1]
		ks2Table.set_index(keys='Dataset',drop=True,inplace=True)
		#construct series to be entered as a row in the dataframe
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
		#print(studentEntry)
		student_df.loc[upn]=studentEntry
		
		#TODO:get grade values, format, enter them into grades_df
		
		gradesTable=pd.read_html(browser.find_element_by_css_selector("#page.closed").get_attribute('innerHTML'),header=0)[10]
		#print(gradesTable.columns)
		gradesTable.columns=gradesTable.columns.str.replace("\n","")
		gradesTable.columns=gradesTable.columns.str.replace("%","")
		gradesTable.columns=gradesTable.columns.str.strip()
		gradesTable['upn']=upn
		del gradesTable['Eligibility']
		del gradesTable['Results Date']
		#print(gradesTable)
		grades_df=grades_df.append(gradesTable)
		#
		
		# if temp_counter>=5:
			# break
		# else:
			# temp_counter+=1
		
	#print(student_df)
	#print(grades_df)
	grades_df['staff']=grades_df['Class'].str.split().str[1:]
	grades_df['Class']=grades_df['Class'].str.split().str[0]
	grades_df['Grade'].fillna("X",inplace=True)
	grades_df['EAP Grade'].fillna("X",inplace=True)
	grades_df['Compare Grade'].fillna("X",inplace=True)
	
	
	
	
	del student_df['attendance']
	del student_df['homestatus']
	
	student_df['ks2_average']=round((student_df['ks2_maths']+student_df['ks2_reading'])*10/2.0)/10.0 #10s needed to get decimal values, floor returns int
	return student_df,grades_df

