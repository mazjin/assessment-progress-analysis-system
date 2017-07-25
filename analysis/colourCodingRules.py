import numpy as np
import pandas as pd

def colour_progress(series):
	"""sets colour coding rules for progress values"""
	#get std dev and average of input series
	sdev=np.std(series)
	savg=np.mean(series)
	
	#setup output list
	output=[]
	#iterate across each element in input series, add colour coding to output
	for index,val in series.iteritems():
		output.append(cc_rules_hilo_avg(val,sdev,savg))
	return output

def colour_progress_df(df):
	#get std dev & average of whole input dataframe
	sdev=df.stack().std()
	savg=df.stack().mean()
	#setup output dataframe
	out=pd.DataFrame(columns=df.columns,index=df.index)
	"""iterate across each element in input dataframe, add colour coding to 
	output"""
	for index,row in df.iterrows():
		for column,val in row.iteritems():
			out.loc[index,column]=cc_rules_hilo_avg(val,sdev,savg)
	return out

def colour_pp_gap(series):
	"""sets colour coding rules for pp gap data"""
	#get std dev of input series
	sdev=np.std(series)
	#setup output list
	output=[]
	#iterate across each element in input series, add colour coding to output
	for index,val in series.iteritems():
		output.append(cc_rules_centre_zero(val,sdev))
	return output

def colour_pp_gap_df(df):
	"""sets colour coding rules for pp gap data"""
	#get std dev of whole input dataframe
	sdev=df.stack().std()
	#setup output dataframe
	out=pd.DataFrame(columns=df.columns,index=df.index)
	#iterate across each element in input dataframe, apply colour coding
	for index,row in df.iterrows():
		for column,val in row.iteritems():
			out.loc[index,column]=cc_rules_centre_zero(val,sdev)
	return out

def cc_rules_centre_zero(val,sdev):
	"""decision making for colour coding centered around 0"""
	#if no value, colour grey
	if val==np.nan:
		return 'background-color:grey'
	#if significantly above/below 0, colour red
	elif val>(sdev) or val<(0-sdev):
		return 'background-color:red'
	#if slightly above/below 0, colour light red
	elif val>(sdev/2) or val<(0-(sdev/2)):
		return 'background-color:#FF8888'
	#otherwise no colour
	else:
		return ''

def cc_rules_hilo_avg(val,sdev,savg):
	"""decision making for colour coding measuring high/low values from
		average"""
	#if no value, colour grey
	if val=="NaN":
		return 'background-color:grey'
	#if value significantly above, colour green
	elif val>(savg+sdev):
		return 'background-color:green'
	#if value significantly below, colour red
	elif val<(savg-sdev):
		return 'background-color:red'
	#otherwise no colour
	else:
		return ''