import data

data.StartDataLogging()

from DataLogger import DataReader

dr=DataReader(settings={'data_root':'/opt/WebSite'})

dr.RebuildCache()

dr.Run()
