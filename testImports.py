"""tests sisraTools importation routines"""
from analysis.sisraTools import *
browser=webdriver.Chrome()
logIntoSISRA("robedw140324","170711Edvs",browser)
openStudentReports(browser,"9","Y9 DD3")
try:
	getStudentData(browser,"9","Y9 DD3")
except:
	browser.close()
	raise
browser.close()