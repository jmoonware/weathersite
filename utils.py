
import numpy as np
import data # the data 'model' 
from datetime import date, timedelta
from datetime import datetime as dt
import pytz
import requests
import time
import settings
import logging
import re
from bs4 import BeautifulSoup as bs

last_update = 0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

remove_tags_pat = r'<[\\/=\-_\w\s]*>'

def update_forecast(*args):
	
	# Get the forecast string from National Weather Service
	forecast_url = settings.forecast_url
	res = None
	forecast_strings = []
	try:
		with requests.Session() as req:
			res = req.get(forecast_url)
		if res:
			soup = bs(res.text,'html.parser')
			fl=soup.find_all(attrs={'class':'forecast-label'})
			ft=soup.find_all(attrs={'class':'forecast-text'})
			for ifl, ift in zip(fl,ft):
				if hasattr(ifl,'text') and hasattr(ift, 'text'):
					forecast_strings.append(': '.join([ifl.text,ift.text]))
	except Exception as ex:
		logging.getLogger(__name__).error("Get Forecast: "+str(ex))

	t = [f for f in forecast_strings if f!=None and len(f) > 0]
	forecast_strings = t

	return forecast_strings

def update_dailyprecip(*args):

	precip_ytd_string = 'None'
	
	# Get the daily precip data and check to see if we have any updates

	earliest_year = 2022
	latest_year = dt.now().year

	# this should load all the data we have
	data_name = 'dailyprecip_in'
	times, readings = data.theDataReader.GetTimestampUTCData(data_name,oldest_hour=24*366*(1+(latest_year-earliest_year)))
	ts_latest_yr = dt(year=latest_year,month=1,day=1).astimezone(pytz.UTC).timestamp()
	
	if len(times)==0 or dt.now(pytz.utc).timestamp()-np.max(times) > 24*3600: 
		dates=[]
		daily_total_precip = []
		precip_url = settings.precip_url
		for yr in range(earliest_year,latest_year+1):
			res = None
			try:
				with requests.Session() as req:
					req.headers.update(headers)
					res = req.get(precip_url.format(yr-2000))
				if res:
					lines=res.text.split('\n')
					for l in lines:
						toks=l.split()
						if len(toks) > 2:
							dates.append(dt.strptime(toks[0],'%m/%d/%y').astimezone(pytz.UTC).timestamp())
							try:
								daily_total_precip.append(float(toks[-2].replace('T','0.001')))
							except:
								daily_total_precip.append(0.0)									
			except Exception as ex:
				logging.getLogger().error("Daily Precip: " + str(ex))

		# if we don't have a record of the lasted downloaded readings, log them now
		rebuild = False
		for d, p in zip(dates,daily_total_precip):
			if not d in times:
				data.theDataWriter.LogData(data_name,p,timestamp=d)
				rebuild = True
		if rebuild:
			time.sleep(5) # wait for some data logging to happen
			data.theDataReader.RebuildCache()
		
		# use the ones we just downloaded
		times = np.array(dates)
		readings = np.array(daily_total_precip)

	total_precip = np.sum(readings[times >= ts_latest_yr])

	precip_ytd_string = "{0:.2f} in".format(total_precip)

	data.theDataReader.ephemera['precipytd_in']=precip_ytd_string

	return precip_ytd_string,


def update_local_thp():
	
	# Get the forecast string from National Weather Service
	forecast_url = settings.forecast_url
	res = None
	thp = {}
	try:
		with requests.Session() as req:
			res = req.get(forecast_url)
		if res:
			soup = bs(res.text,'html.parser')
			ts=soup.find_all(attrs={'class':'myforecast-current-lrg'})
			if ts and len(ts)>0 and hasattr(ts[0],'text'):
				floatval = clean_float_string(ts[0].text,rchars=[u"\u00B0",'F'])
				thp['{0}_T_F'.format(settings.origins.nws_tla)]=floatval
			ltab=soup.find_all(attrs={'id':'current_conditions_detail'})
			tok_pairs = [x.text for x in ltab[0].find_all('td')]
			hkey = None
			pkey = None
			if int(len(tok_pairs))%2 == 0:
				for i in range(int(len(tok_pairs)/2)):
					key = settings.origins.nws_tla+'_'+tok_pairs[2*i].lower().replace(' ','_') 
					thp[key]=tok_pairs[2*i+1].strip()
					if 'humidity' in key:
						hkey = key
					elif 'barometer' in key:
						pkey = key
			if hkey and hkey in thp:
				thp[hkey.replace("humidity","H")+"_perc"]=clean_float_string(thp[hkey],rchars=['%'])
				del thp[hkey]
			if pkey and pkey in thp:
				thp[pkey.replace("barometer","P")+"_inHg"]=clean_float_string(thp[pkey].split(' ')[0],rchars=['i','n'])
				del thp[pkey]
	except Exception as ex:
		logging.getLogger(__name__).error("Get NWS THP: "+str(ex))

	return thp

def clean_float_string(s,rchars=[],chopend=0,default_val=-999.):
	''' utility function to convert strings with dangly stuff and weird
		chars to strings that can be converted to float values
	'''
	ntok = s
	if chopend > 0:
		ntok=s[:chopend]
	for c in rchars:
		ntok=ntok.replace(c,'')
	floatval = default_val
	try:
		floatval=float(ntok)
	except ValueError as ve:
		logging.getLogger(__name__).error("utils:clean_float_string: {0}".format(ve))
	return(ntok)

