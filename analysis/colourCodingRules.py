import numpy as np

def colour_progress(series):
		sdev=np.std(series)/2.0
		savg=np.mean(series)
		print(sdev,savg)
		output=[]
		for index,val in series.iteritems():
			if val=="NaN":
				output.append('background-color:grey')
			elif val>(savg+sdev):
				output.append('background-color:green')
			elif val<(savg-sdev):
				output.append('background-color:red')
			else:
				output.append('background-color:yellow')
		#is_high=series<(savg+sdev)
		return output