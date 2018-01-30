import numpy as np
import pandas as pd

set_colours={"red":"#FF0000",
	"amber":"#FFCC00",
	"ligreen":"#99CC00",
	"fgreen":"#008800",
	}

def colour_progress(obj):
	"""colours series or DataFrame based on std dev of whole object and distance
	 from mean of object by calling cc_rules_hilo_avg - general default"""
	if isinstance(obj,pd.DataFrame):
		odev=obj.stack().std()
		oavg=obj.stack().mean()
	else:
		odev=obj.std()
		oavg=obj.mean()
	return obj.apply(cc_rules_hilo_avg,dev=odev,avg=oavg)

def colour_gap(obj):
	"""colours series or DataFrame based on std dev of whole object and distance
	 from zero by calling cc_rules_centre_zero - used on gap data"""
	if isinstance(obj,pd.DataFrame):
		odev=obj.stack().std()
	else:
		odev=obj.std()
	return obj.apply(cc_rules_centre_zero,dev=odev)

def colour_mixed(obj):
	"""colours DataFrame with mixed types of data using cc_rules_hilo_avg, std
	dev of each column and distance from mean of each column - used for
	attainment sheets"""
	out=pd.DataFrame(columns=obj.columns,index=obj.index)
	for colname,colseries in obj.iteritems():
		if "#" in colname:
			out[colname]=["" for i in range(colseries.count())]
		else:
			cdev=colseries.std()
			cavg=colseries["All"]
			out[colname]=colseries.apply(cc_rules_hilo_avg,dev=cdev,avg=cavg)
	return out


def cc_rules_centre_zero(val,**kwargs):
	"""decision making for colour coding centered around 0"""
	sdev=kwargs['dev']

	#if passed series instead of values, applies recursively to series values
	if isinstance(val,pd.Series):
		return val.apply(cc_rules_centre_zero,dev=sdev)
	else:
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

def cc_rules_hilo_avg(val,**kwargs):
	"""decision making for colour coding measuring high/low values from
		average"""
	sdev=kwargs['dev']
	savg=kwargs['avg']

	#if passed series instead of values, applies recursively to series values
	if isinstance(val,pd.Series):
		return val.apply(cc_rules_hilo_avg,dev=sdev,avg=savg)
	else:
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

def colour_eap(input_obj,exc):
	if exc:
		output=['background-color:grey' if (str(x)=="" or x==None \
			or str(x)=="nan") \
		else 'background-color:' +set_colours['red'] if float(x) <0 \
		else 'background-color:' +set_colours['amber'] if float(x) < 5 \
		else 'background-color:' +set_colours['fgreen'] if float(x)==30 \
		else 'background-color:' +set_colours['ligreen'] if float(x)>15 \
		else "" for x in input_obj]
	else:
		output=['background-color:grey' if (str(x)=="" or x==None \
			or str(x)=="nan") \
		else 'background-color:' +set_colours['red'] if float(x) <=80 \
		else 'background-color:' +set_colours['amber'] if float(x) < 85 \
		else 'background-color:' +set_colours['fgreen'] if float(x)>=100 \
		else 'background-color:' +set_colours['ligreen'] if float(x)>95 \
		else "" for x in input_obj]
	return output
