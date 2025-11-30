import logging
from autopool.logic.command import Command
from autopool.commands.DataLogger import DataWriter
from autopool.commands.DataLogger import DataReader
from datetime import datetime as dt
import time
import pytz
import os
import numpy as np
import requests
import re

origin_hourly = 'precip_inphr'

class LogWebCommand(Command):
	def Init(self):
		self.blocking=False
		self.loop_count=-1
		self.loop_interval=30
		self.hourly_precip_url='https://www.weather.gov/source/sgx/hydro/LAXRRMSAN'
		self.station='RNBC1' # Rancho Bernardo
		self.tpat='PERIODS ENDING AT[ ]+([0-9]+)[ ]+([AP]M)'
	def Execute(self):
		r=None
		with requests.Session() as req:
			r = req.get(self.hourly_precip_url)

		precip_1hr = 0
		utc_log_timestamp=0
		if r:
			for line in r.text.split('\n'):
				# search for time pattern
				sr=re.search(self.tpat, line.upper())
				if sr and len(sr.groups())==2:
					self.logger.debug("*** " + sr.groups()[0] + sr.groups()[1])
					log_hour=int(sr.groups()[0])
					if log_hour==12 and sr.groups()[1]=='AM':
						log_hour=0
					if sr.groups()[1]=='PM' and log_hour < 12:
						log_hour+=12
					# local_now in same time zone as forecast
					# todo: adjust for possible different time zones
					local_now = dt.now()
					utc_log_timestamp = dt(
						year=local_now.year,
						month=local_now.month,
						day=local_now.day,
						hour=log_hour).astimezone(pytz.utc).timestamp()
				if self.station in line and len(line) > 38:
					station_check = line[0:5].strip()
					station_name = line[6:27].strip()
					elev = line[28:32].strip()
					precip_1hr = float(line[33:38].strip().replace('T','0.001'))
					self.logger.debug("=".join([station_check,station_name,elev,str(precip_1hr)]))
		self.logger.debug("One hour precip={0} in/hr for {1}".format(precip_1hr,self.station))
		reading=[]
#		reading=self.data_reader.GetLatestReadings(origin_hourly)
#		self.logger.debug(str(self.data_reader.GetLatestReadings()))
		if len(reading)==0: # no reading
			self.logger.debug("No readings - log {0},{1}".format(utc_log_timestamp,precip_1hr))
#			self.data_logger.LogData(origin_hourly,precip_1hr,timestamp=utc_log_timestamp)
			# KLUDGE: wait for data_logger to get data on disk
#			time.sleep(3*self.data_logger.loop_interval)
#			self.data_reader.RebuildCache()	
		elif 'time' in reading[origin_hourly] and utc_log_timestamp > reading[origin_hourly]['time']:
			self.logger.debug("New hourly value - log {0},{1} (latest logged timestamp {2})".format(utc_log_timestamp,precip_1hr,reading[origin_hourly]['time']))
#			self.data_logger.LogData(origin_hourly,precip_1hr,timestamp=utc_log_timestamp)
		else:
			self.logger.debug("Same value at {0},{1} {2}".format(utc_log_timestamp,precip_1hr,reading))
			

