import numpy as np

def colour_progress(series):
	"""sets colour coding rules for progress values"""
	sdev=np.std(series)
	savg=np.mean(series)
	output=[]
	for index,val in series.iteritems():
		#if no value, colour grey
		if val=="NaN":
			output.append('background-color:grey')
		#if value significantly above, colour green
		elif val>(savg+sdev):
			output.append('background-color:green')
		#if value significantly below, colour red
		elif val<(savg-sdev):
			output.append('background-color:red')
		#otherwise no colour
		else:
			output.append('')
	return output