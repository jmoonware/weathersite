from worker import Worker
import os
from datetime import datetime as dt
from datetime import timedelta
from collections import deque,OrderedDict # deque is thread-safe as used here
import requests
import logging
import glob
import numpy as np
import pytz
import re
import json
import portalocker # needed for cross-process awareness
import threading

# Flat file data logger
# organizes data by {root}/YYYY/Mon/Day/{fn}.dat
# {root} is absolute file path
# Filename convention is <Device><Measurement>.dat (can be any string)
# File format is <float_timestamp .3f>{data_sep}<float_value .3f>{eol}
#
# rest_url is a custom website that logs data on a get request using
# a short query string on the endpoint /sensors
# e.g.
# http://ec2.xxx/sensors/wind_angle?time=23948&reading=23.5
# 

data_sep="\t"
data_ext=".dat"
report_timezone="US/Pacific"

#
# max_data_cache is the number of ~16 byte (2 Python floats) held in memory for each
# for logging at 1 s intervals, data accumulates at ~80k s*16 bytes=1.3 MB/day per measurement
# 
max_data_cache=10000000

# utility for getting file name from path, date, origin
def file_for_date(data_root,c_dt,origin,ext='.dat'):
	return(os.path.join(data_root,str(c_dt.year),str(c_dt.month),str(c_dt.day),origin+'.dat'))


class DataWriter(Worker):
	def Init(self):
		self.loop_count=-1
		self.blocking=False
		self.loop_interval=1
		if not 'data_root' in self.__dict__.keys():
			self.data_root="" # execution folder
		if not 'data_url' in self.__dict__.keys():
			self.data_url=None # ignore
		self.data_values={} # to be logged
		self.data_sync=threading.Lock() # need to lock top-level value,cache dicts while modifying with new origins

		# make sure we have write access to root 
		# if any of these throw an exception then handle here
		try:
			if not os.path.isdir(self.data_root):
				os.makedirs(self.data_root)	
			tfile=os.path.join(self.data_root,'delete.me')
			with open(tfile,'w') as f:
				f.write('#') # arbitrary; just makes sure file is there
			os.remove(tfile)
		except OSError as ox:
			self.logger.debug("Failed to gain write access to {0}".format(self.data_root))
			self.data_root=None # will cause exceptions down the line if used


	def LogData(self,origin,value,timestamp=None,precision=3):
		if not origin in self.data_values:
			with self.data_sync:
				self.data_values[origin]=deque()
		if timestamp == None:
			ts=dt.timestamp(dt.now(pytz.utc))
		else:
			ts=timestamp
		self.data_values[origin].append([float(ts),float(value),precision])
	def Execute(self):
		# this is where data gets logged periodically
		# since this could be in a completely separate process, made this process aware, which is where the 
		# complexity arises in the data reader
		# note that since every new data timestamp might change the directory boundary, have to check each and every time
		# we log a new timestamp, reading pair			
		for origin in self.safe_dict(self.data_values):
			pairs_for_url=[]
			if len(self.data_values[origin]) > 0:
				data_path=file_for_date(self.data_root,dt.utcfromtimestamp(self.data_values[origin][0][0]),origin)
				self.logger.debug("{0} Writing {1} data pairs to (initially) {2}".format(self,len(self.data_values[origin]),data_path))
				while len(self.data_values[origin]) > 0:
					pair_to_write=self.data_values[origin].popleft()
					fmt="{0:.3f}"+data_sep+"{1:."+str(pair_to_write[2])+"e}\n"
					data_path=file_for_date(self.data_root,dt.utcfromtimestamp(pair_to_write[0]),origin)
					dpath=os.path.dirname(data_path)
					if not os.path.isdir(dpath): # small chance some other proc is making these as we check...
						os.makedirs(dpath,exist_ok=True)
					with portalocker.Lock(data_path,'a+b',timeout=5) as f:
						f.write(fmt.format(pair_to_write[0],pair_to_write[1]).encode('utf-8'))
						pairs_for_url.append(pair_to_write)
			# try to upload
			if self.data_url:
				# todo: aggregate in one request
				for ptw in pairs_for_url:
					url=self.data_url+"/"+origin
					payload={'time':str(ptw[0]),'reading':str(ptw[1])}
					try:
						requests.get(url,params=payload,timeout=2)
					except Exception as ex:
						self.logger.error("{0} Error data logging to {1}: {2}".format(self,self.data_url,ex))

	# make a thread-safe copy - since there aren't very many origins this should be pretty fast
	# the underlying items in the data dicts are usually deque's which should be thread-safe as used in the writer
	def safe_dict(self,d):
		ret={}
		with self.data_sync:
			for k in d:
				ret[k]=d[k]
		return(ret)
		

				
# utility class to read data back into memory from disk
class DataReader(Worker):
	def Init(self):
		self.loop_count=-1
		self.blocking=False
		self.loop_interval=1	
		if not 'data_root' in self.__dict__.keys():
			self.data_root="" # execution folder
		self.dates={}
		self.filenames={} # by origin, then by sorted date
		self.data_cache={} # recent values held in memory
		self.ephemera={} # general purpose transient values
		self.stats_cache={}
		self.today_filesize={} # file size for this day at last write, by origin
		self.stats_interval=60 # FIXME about every minute
		self.stats_interval_counter=self.stats_interval
		self.data_sync=threading.Lock() # keeps Get functions and Execute/Update functions from races
		self.stats_sync=threading.Lock() # keeps Get functions and Execute/Update functions from races
		self.file_size_sync=threading.Lock() # need to lock top-level value,cache dicts while modifying with new origins

	def Execute(self):
		# this is where data gets logged periodically
		# since this could be in a completely separate process, made this process aware, which is where the 
		# complexity arises in the data reader
		# first, make sure directories are there (in correct time zone!)
		now=dt.now(pytz.utc)

		# look for data from another process - lock in function
		self.UpdateTodaysCache(now)
	
		# possibly trim size of data cache - we are locked here
		with self.data_sync:
			for origin in self.data_cache:
				while len(self.data_cache[origin]['time']) >= max_data_cache: # delete values from cache
					self.data_cache[origin]['time'].popleft()
					self.data_cache[origin]['reading'].popleft()
			
			
		self.stats_interval_counter-=1
		if self.stats_interval_counter<=0:
			self.stats_interval_counter=self.stats_interval
			# invalidate today's stats and recalculate
			today_ts=dt(year=now.year,month=now.month,day=now.day).replace(tzinfo=pytz.utc).timestamp()
			with self.stats_sync:
				for origin in self.stats_cache:
					if today_ts in self.stats_cache[origin]:
						self.logger.debug("Updating daily statistics for {0} {1}...".format(origin,dt.utcfromtimestamp(today_ts).isoformat()))
						del self.stats_cache[origin][today_ts]
						self.UpdateStats(origin=origin,date_ts=today_ts)
			self.logger.debug("{0} Updating statistics...".format(self))
			with self.stats_sync:
				self.UpdateStats()

	# called once on start-up, although this could be used to reset cache as well
	# generally don't call this in Init() so that the logger is running
	def RebuildCache(self,max_hours=72):
		# rebuild cache

		self.UpdateAvailableDatFiles()

		for origin in self.origins:
			t,r=self.GetTimestampUTCData(origin,oldest_hour=max_hours) # load in past 3 days by default
			with self.data_sync: # generally won't need as only called before Execute starts or anyone is asking for data
				self.data_cache[origin]={'time':deque(t),'reading':deque(r)}

		with self.stats_sync:
			self.UpdateStats()

	def UpdateTodaysCache(self,now):
		for origin in self.data_cache:
			data_path=file_for_date(self.data_root,now,origin)
			if os.path.isfile(data_path): # the latest data file exists
				if origin in self.today_filesize: # we've read this file before
					with self.file_size_sync:
						tsize=os.path.getsize(data_path)
						newlines=[]
						if tsize > self.today_filesize[origin]: # another process wrote to the file
							self.logger.debug("{0} updating data from another process".format(self))
							with portalocker.Lock(data_path,'rb',timeout=5) as f:
								f.seek(self.today_filesize[origin]) # seek to where we left off
								newlines=f.readlines()
							self.logger.debug("{0} seek={1}, tsize={2}, newlines={3}".format(self,self.today_filesize[origin],tsize,newlines))
							self.today_filesize[origin]=tsize # this is now the latest file size we have read
						with self.data_sync:
							# this appends the new lines another process wrote
							self.ParseLines(newlines,self.data_cache[origin]['time'],self.data_cache[origin]['reading'])	
				else: # have a file, but no previous read	
					with self.file_size_sync:				
						self.today_filesize[origin]=0
			else: # no file yet
				with self.file_size_sync:
					self.today_filesize[origin]=0

	# data for callback on real-time gauges
	def GetLatestReadings(self,origin=None):
		ret={}
		if not origin: # return for all origins
			for origin in self.data_cache:
				if 'time' in self.data_cache[origin] and len(self.data_cache[origin])>0:
					if len(self.data_cache[origin]['time']) > 0:
						ret[origin]={'time':self.data_cache[origin]['time'][-1],'reading':self.data_cache[origin]['reading'][-1]}
		elif origin in self.data_cache:
			if len(self.data_cache[origin]['time']) > 0:
				ret[origin]={'time':self.data_cache[origin]['time'][-1],'reading':self.data_cache[origin]['reading'][-1]}
		return(ret)
		
	# here is were we get the latest t,r data for plotting in the callbacks		
	def GetCacheData(self,origin,newest_hour=0,oldest_hour=24,in_cache=False):
		if origin==None:
			self.logger.debug("Get Data: origin is none")
			return [],[]
		t,r=self.GetTimestampUTCData(origin,newest_hour=newest_hour,oldest_hour=oldest_hour,in_cache=in_cache)
		# convert t to iso format strings in PTZ for graphing
		# TODO: optimize this monstrosity
		t_iso=[dt.utcfromtimestamp(ti).replace(tzinfo=pytz.UTC).astimezone(tz=pytz.timezone(report_timezone)).isoformat() for ti in t]
		return t_iso,r

	# Returns cached summary stats for an origin
	# format is t: iso-strings for corresponding daily or hourly stats
	# stats is a dictionary with descriptiveStats keys (i.e. 'min','max', etc.) where each value is an array
	# with a point corresponding to the time array
	# start_time_utc is a datetime object; 'now' if not supplied
	# Note: should be thread safe as we only read from dict, not iterate
	def GetCacheStats(self,origin,start_time_utc=None,newest_hour=0,oldest_hour=24,hourly=True):
		with self.stats_sync:
			if origin==None:
				self.logger.debug("GetCacheStats: origin is none")
				return [],{}
			stats={}
			t=[]
			keys=['N','min','mintime','max','maxtime','p25','p50','p75','mean','std']
			for k in keys:
				stats[k]=[]

			if origin in self.stats_cache:
				if start_time_utc==None: # get today's date
					start_time_utc=dt.now(pytz.utc).replace(tzinfo=pytz.UTC)
			else:
				self.logger.debug("GetCacheStats: origin not in cache")
				return [],{}
			# closest hour
			start_hour_dt=dt(start_time_utc.year,start_time_utc.month,start_time_utc.day,start_time_utc.hour).replace(tzinfo=pytz.UTC)
			
			end_hour_dt=start_hour_dt-timedelta(hours=oldest_hour)
			end_date=dt(year=end_hour_dt.year,month=end_hour_dt.month,day=end_hour_dt.day).replace(tzinfo=pytz.UTC)
			num_days=int(np.ceil((start_hour_dt-end_hour_dt).total_seconds()/(3600*24)))
			
			if hourly:
				for d in range(num_days): # count oldest to youngest
					for h in range(24):
						c_hour=d*24+h
						c_dt=end_hour_dt+timedelta(hours=c_hour)
						date_index=dt(year=c_dt.year,month=c_dt.month,day=c_dt.day).replace(tzinfo=pytz.UTC).timestamp()
#						print(c_dt,h)
						if date_index in self.stats_cache[origin]: # have stats for this date
							# json deserialize makes this a string
							if str(c_dt.hour) in self.stats_cache[origin][date_index]['hourly']:
								t.append(c_dt.timestamp())
								for k in keys:
									stats[k].append(self.stats_cache[origin][date_index]['hourly'][str(c_dt.hour)][k])
						if c_hour>=oldest_hour: # counted enough hours
							break

			else: # FIXME: currently boundary aligned to UTC clock, not local time
				for d in range(num_days):
					c_dt=start_hour_dt-timedelta(hours=d*24)
					date_index=dt(year=c_dt.year,month=c_dt.month,day=c_dt.day).replace(tzinfo=pytz.UTC).timestamp()
					if date_index in self.stats_cache[origin]: # have stats for this date
						t.append(date_index)
						for k in keys:
							stats[k].append(self.stats_cache[origin][date_index]['daily'][k])
									
				
		# TODO: optimize this monstrosity
		t_iso=[dt.utcfromtimestamp(ti).replace(tzinfo=pytz.UTC).astimezone(tz=pytz.timezone(report_timezone)).isoformat() for ti in t]
		
		return t_iso,stats
		
	def GetTimestampUTCData(self,origin,newest_hour=0,oldest_hour=24,in_cache=False):
		now=dt.now(pytz.utc)
		newest_dt=now-timedelta(hours=newest_hour)
		newest_ts=newest_dt.timestamp()
		oldest_dt=now-timedelta(hours=oldest_hour)
		oldest_ts=oldest_dt.timestamp()
		# look in cache first
		t=np.array([])
		r=np.array([])
		if origin in self.data_cache.keys():
			with self.data_sync: # avoid possible race with Execute/Update
				t=np.array(self.data_cache[origin]['time'])
				r=np.array(self.data_cache[origin]['reading'])
			if in_cache: # just return current cache contents - for debugging
				return(t,r)
			# this succeeds if we happen to be looking at the latest data put in by Rebuild and Update
			if len(t) > 0 and oldest_ts>=t[0] and (newest_hour<=0 or newest_ts <= t[-1]): # we have all the data in cache
#				logging.getLogger(__name__).debug("{0} Get data (cache)".format(self))
				return(t[(t>=oldest_ts)*(t<=newest_ts)],r[(t>=oldest_ts)*(t<=newest_ts)])

		# load fresh from disk
		# TODO: add to cache, although without some complex logic cache fragmentation could occur
		data_dict=self.GetDataFromDisk({origin:self.calculate_possible_files_from_date(origin,newest_dt,oldest_dt)})

		if origin in data_dict:
			t=np.array(data_dict[origin]['time'])
			r=np.array(data_dict[origin]['reading'])
			if len(t)==0:
				self.logger.debug("{0} Zero length data for {1}".format(self,origin))
			elif oldest_ts >=t[0] and (newest_hour <= 0 or newest_ts <= t[-1]): # we have all the data from file
				logging.getLogger(__name__).debug("{0} Get data latest (file)".format(self))
				return(t[(t>=oldest_ts)*(t<=newest_ts)],r[(t>=oldest_ts)*(t<=newest_ts)])
		# just return whatever we have
		logging.getLogger(__name__).debug("{0} Get data (whatever we have)".format(self))
		return(t[(t>=oldest_ts)*(t<=newest_ts)],r[(t>=oldest_ts)*(t<=newest_ts)])
		
	# calculates list of possible cache files within a date range
	def calculate_possible_files_from_date(self,origin,newest_dt,oldest_dt):
		numdays=int((newest_dt-oldest_dt).days)
		files=[]
		for i in range(numdays+1):
			c_dt=oldest_dt+timedelta(days=i)
			logging.getLogger(__name__).debug("{0} Will try file {1}".format(self,file_for_date(self.data_root,c_dt,origin)))
			files.append(file_for_date(self.data_root,c_dt,origin))
		return(files)

	# Updates should only be called in Execute where there is a sync
	def UpdateStats(self,origin=None,date_ts=None):
		if origin==None and date_ts==None:
			self.UpdateAvailableDatFiles()
			tfns=self.filenames
			tdates=self.dates
			force=False
		else: # force update of specific single origin and date
			c_dt=dt.utcfromtimestamp(date_ts).replace(tzinfo=pytz.utc)
			tfns={origin:[file_for_date(self.data_root,c_dt,origin)]}
			tdates={origin:[date_ts]}
			force=True
		for origin in tfns:
			if not origin in self.stats_cache:
				self.stats_cache[origin]=OrderedDict() # by date
			for fn,d in zip(tfns[origin],tdates[origin]):
				if not d in self.stats_cache[origin]: # if it is in the cache assume it is good
					statfn=fn.replace(data_ext,".json")
					if os.path.isfile(statfn) and not force: # already calculated
						with portalocker.Lock(statfn,'r',timeout=5) as f:
							self.stats_cache[origin][d]=json.load(f)
					else: # need to recalculate
						tdat={'time':[],'reading':[]}
						if os.path.isfile(fn): 
							with portalocker.Lock(fn,'r',timeout=5) as f:
								lines=f.readlines()
							tdat['time']=[float(l.split(data_sep)[0]) for l in lines]
							tdat['reading']=[float(l.strip().split(data_sep)[1]) for l in lines]
							self.stats_cache[origin][d]=self.CalculateStats(tdat,d)
							if len(self.stats_cache[origin][d]['daily'])==0: # don't write empty stats
								del self.stats_cache[origin][d]
							else:
								with portalocker.Lock(statfn,'w',timeout=5) as f:
									json.dump(self.stats_cache[origin][d],f,indent=2)

	# date_ts should be 00:00:00 (hh:mm:ss) of the current utc date
	def CalculateStats(self,data,date_ts): 
		ret={}
		date=dt.utcfromtimestamp(date_ts).replace(tzinfo=pytz.utc)
		ret['date']=dt.utcfromtimestamp(date_ts).replace(tzinfo=pytz.utc).date().isoformat()
		tmin=date_ts
		tmax=(date+timedelta(hours=24)).replace(tzinfo=pytz.utc).timestamp()
		ret['daily']=self.descriptiveStats(data,tmin,tmax)
		ret['hourly']={}
		for h in range(24):
			tmin=(date+timedelta(hours=h)).replace(tzinfo=pytz.utc).timestamp()
			tmax=(date+timedelta(hours=h+1)).replace(tzinfo=pytz.utc).timestamp()
			ret['hourly'][str(h)]=self.descriptiveStats(data,tmin,tmax)
			if len(ret['hourly'][str(h)])==0: # no data to compute in this time window
				del ret['hourly'][str(h)]

		return(ret)
		
	def descriptiveStats(self,data,tmin,tmax):
		ret={}
		readings=np.array(data['reading'])
		times=np.array(data['time'])
		sub_readings=readings[(times>=tmin)*(times<=tmax)]
		sub_times=times[(times>=tmin)*(times<=tmax)]
		if len(sub_readings) > 0:
			ret['N']=len(sub_readings)
			ret['min']=np.min(sub_readings)
			ret['mintime']=sub_times[np.argmin(sub_readings)]
			ret['max']=np.max(sub_readings)
			ret['maxtime']=sub_times[np.argmax(sub_readings)]
			ret['p25']=np.percentile(sub_readings,25)
			ret['p50']=np.percentile(sub_readings,50)
			ret['p75']=np.percentile(sub_readings,75)	
			ret['mean']=np.mean(sub_readings)
			ret['std']=np.std(sub_readings)
		return(ret)

	# Gets an indpendent de novo copy of data from disk
	def GetDataFromDisk(self,files): 

		# fresh copy
		data_dict={}
		for origin in files:
			latest_file=file_for_date(self.data_root,dt.now(pytz.utc),origin)
			for fn in files[origin]:
				if not os.path.isfile(fn):
					logging.getLogger(__name__).debug("DataReader Skipping non-existent file {0}".format(fn))
				else:
					logging.getLogger(__name__).debug("DataReader Read {0}".format(fn))
					sz=0
					with portalocker.Lock(fn,'rb',timeout=5) as f:
						lines=f.readlines()
						sz=f.tell() # this should be the accurate size we just read, no one can write to it in lock
					if fn==latest_file: # track latest file size
						with self.file_size_sync: # don't unexpectedly change stored file size
							self.today_filesize[origin]=sz
					if not origin in data_dict:
						data_dict[origin]={'time':[],'reading':[]}
					self.ParseLines(lines,data_dict[origin]['time'],data_dict[origin]['reading'])
		return data_dict
		
	def ParseLines(self,lines,time_list,reading_list):
		for l in lines:
			vals = l.decode('utf-8').strip().split(data_sep)
			if len(vals)==2:
				time_list.append(float(vals[0]))
				reading_list.append(float(vals[1]))
		return
		
	def UpdateAvailableDatFiles(self,single_origin=None):
		# get all the availalalbe .dat origins, will filter below
		if not single_origin:
			self.origins=[]
			dp=os.path.join(self.data_root,"**","*"+data_ext)
			fns=glob.glob(dp,recursive=True)
			for fn in fns: 
				origin=os.path.splitext(os.path.basename(fn))[0]
				if origin not in self.origins:
					self.origins.append(origin)
			origins=self.origins
		else:
			origins=[single_origin]
			
		self.dates={}
		self.filenames={}
		for origin in origins:
			self.dates[origin]=[]
			self.filenames[origin]=[]
			dp=os.path.join(self.data_root,"**",origin+data_ext)
			fn=glob.glob(dp,recursive=True)
			# now construct datetime pattern, and sort
			for f in fn:
				toks=f.split(os.sep)
				if len(toks) > 3: # check format
					if  re.search("^20[0-9][0-9]$",toks[-4])!=None and re.search("^[0-9]{1,2}$",toks[-3])!=None and re.search("^[0-9]{1,2}$",toks[-2])!=None:
						year=int(toks[-4])
						mon=int(toks[-3])
						day=int(toks[-2])
						self.dates[origin].append(dt(year=year,month=mon,day=day).replace(tzinfo=pytz.utc).timestamp())
						self.filenames[origin].append(f)
					else:
						self.origins.remove(origin)
			idx=np.argsort(self.dates[origin])
			fn_sort=[self.filenames[origin][i] for i in idx]
			self.filenames[origin]=fn_sort
			self.dates[origin].sort() # sort the dates too
			

