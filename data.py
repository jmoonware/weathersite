import pandas as pd
import os
import numpy as np
import json
from datetime import datetime
import logging
import logging.handlers
from importlib import reload
from DataLogger import DataReader,DataWriter
import settings

# note: Dash can start multiple instances of these!
theDataWriter=None
theDataReader=None

def StartDataLogging():
	global theDataWriter
	global theDataReader
	theDataWriter=DataWriter(settings={'data_root':settings.data_root})
	theDataReader=DataReader(settings={'data_root':settings.data_root})
	logFormatString='\t'.join(['%(asctime)s','%(levelname)s','%(message)s'])
	level=logging.DEBUG
	addr=theDataWriter.__repr__().split('.')[-1].split(' ')[-1].split('>')[0]
	filename=settings.log_path.split('.txt')[0]+addr+'.txt' # unique-ish log name every startover
	maxbytes=10000000
	rfh=logging.handlers.RotatingFileHandler(filename=filename,maxBytes=maxbytes,backupCount=10)
	sh=logging.StreamHandler()
	logging.basicConfig(format=logFormatString,handlers=[sh,rfh],level=level)
	logging.captureWarnings(True)
	logger=logging.getLogger(__name__)
	logger.critical("Logging Started, level={0}".format(level))
	theDataReader.RebuildCache()
	theDataReader.Run()
	theDataWriter.Run()

def GetDataFrame():
	init_data={'x':[1,2,3],'y':[2,3,5]}
	return(pd.DataFrame(init_data))
	
def GetPlotData(df):
	return([dict(x=df['x'],y=df['y'])])
	
