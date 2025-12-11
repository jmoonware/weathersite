
import numpy as np
import data # the data 'model' 
from datetime import date, timedelta
from datetime import datetime as dt
import pytz
import requests
import time
import settings
import logging

last_update = 0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

def update_forecast(*args):
	forecast_string = 'None'
	forecast_string_1 = 'None'
	
	# Get the forecast string from National Weather Service
	forecast_url = settings.forecast_url
	res = None
	forecast_strings = []
	try:
		with requests.Session() as req:
			res = req.get(forecast_url)
		if res:
			lines=res.text.split('\n')
			fc = [l for l in lines if 'period-name' in l]
			if len(fc) == 1:
				forecast_strings = [l.split('title=')[0].replace('"','').strip  () for l in fc[0].split('alt=')[1:]]
			elif len(fc) == 2:
				forecast_strings = [l.split('title=')[0].replace('"','').strip  () for l in fc[1].split('alt=')[1:]]
			else: # old format
				for l,nl in zip(lines[:-1],lines[1:]):
					if 'period-name' in l:
						fs = nl.split('title=')[1].split('class')[0].strip().replace('"','')
						if len(fs) > 0:
							forecast_strings.append(fs)
	except Exception as ex:
		pass

	t = [f for f in forecast_strings if f!=None and len(f) > 0]
	forecast_strings = t
	for ifs, fs in enumerate(forecast_strings):
		data.theDataReader.ephemera['Forecast{0}'.format(ifs)]=fs

	if len(forecast_strings) > 1:
		forecast_string = forecast_strings[0]
		forecast_string_1 = forecast_strings[1]

	return forecast_string, forecast_string_1

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

