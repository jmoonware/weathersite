import sys

sys.path.append("..")

import data
import settings
import time

data.StartDataLogging()

data_url = 'http://localhost:8050/sensors'

from DataLogger import DataReader, DataWriter

dr=DataReader(settings={'data_root':'../../../test/logger/data'})
dw=DataWriter(settings={'data_root':'../../../test/logger/data','data_url':data_url})

dr.RebuildCache()

dr.Run()
dw.Run()

dw.LogData(settings.origins.wind_speed,"20")
dw.LogData(settings.origins.wind_speed,"30")
dw.LogData(settings.origins.wind_speed,"40")

dw.LogData(settings.origins.wind_angle,"120")
dw.LogData(settings.origins.wind_angle,"100")
dw.LogData(settings.origins.wind_angle,"90")

time.sleep(2)

print(dr.GetLatestReadings())
