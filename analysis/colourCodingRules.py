import numpy as np
import pandas as pd

set_colours={"red":"#FF0000",
	"amber":"#FFCC00",
	"ligreen":"#99CC00",
	"fgreen":"#008800",
	}

def colour_progress(series):
	"""sets colour coding rules for progress values"""
	#get std dev and average of input series
	sdev=np.std(series)
	savg=np.mean(series)

	#setup output list
	output=[]
	#iterate across each element in input series, add colour coding to output
	if series.name=="#":
		#exempt pupil count columns from being colour coded
		output=["" for i in range(series.count())]
	else:
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
	if str(val)=="nan" or str(val)=="NaN" or str(val)=="" or val==None:
		return "background-color:grey"
	#if exactly zero, forest green
	elif val ==0:
		return "background-color:" + set_colours['fgreen']
	#if close to 0, light green
	elif val<(sdev/10) and val>(0-(sdev/10)):
		return "background-color:" + set_colours['ligreen']
	#if significantly above/below 0, colour red
	elif val>(sdev) or val<(0-sdev):
		return "background-color:" + set_colours['red']
	#if slightly above/below 0, colour amber
	elif val>(sdev/2) or val<(0-(sdev/2)):
		return "background-color:" + set_colours['amber']
	#otherwise no colour
	else:
		return ''

def cc_rules_hilo_avg(val,sdev,savg):
	"""decision making for colour coding measuring high/low values from
		average"""
	#if no value, colour grey
	if str(val)=="nan" or str(val)=="NaN" or str(val)=="" or val==None:
		return "background-color:grey"
	#if value significantly above, colour forest green
	elif val>(savg+sdev):
		return "background-color:" + set_colours['fgreen']
	#if value somewhat above, colour light green
	elif val>(savg+(sdev/2)):
		return "background-color:" + set_colours['ligreen']
	#if value significantly below, colour red
	elif val<(savg-sdev):
		return "background-color:" + set_colours['red']
	#if value somewhat below, colour amber
	elif val<(savg-(sdev/2)):
		return "background-color:" + set_colours['amber']
	#otherwise no colour
	else:
		return ''

def colour_mx_EAP(input_obj):
	"""colours series based on % meeting or exceeding EAP"""
	if ">=" in input_obj.name:
		output=['background-color:grey' if (str(x)=="" or x==None \
			or str(x)=="nan") \
		else 'background-color:' +set_colours['red'] if float(x) <80 \
		else 'background-color:' +set_colours['amber'] if float(x) < 85 \
		else 'background-color:' +set_colours['fgreen'] if float(x)==100 \
		else 'background-color:' +set_colours['ligreen'] if float(x)>95 \
		else "" for x in input_obj]
	else:
		output=['background-color:grey' if (str(x)=="" or x==None \
			or str(x)=="nan") \
		else 'background-color:' +set_colours['red'] if float(x) ==0 \
		else 'background-color:' +set_colours['amber'] if float(x) < 5 \
		else 'background-color:' +set_colours['fgreen'] if float(x)>=30 \
		else 'background-color:' +set_colours['ligreen'] if float(x)>15 \
		else "" for x in input_obj]
	return output
