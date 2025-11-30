import sys

sys.path.append("..")

import data

data.StartDataLogging()

from DataLogger import DataReader

dr=DataReader(settings={'data_root':'../../test/data'})

dr.RebuildCache()

dr.Run()
