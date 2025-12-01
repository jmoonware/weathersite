import sys

sys.path.append("..")

import data
import utils
import settings
import time

data.StartDataLogging()

print(utils.update_dailyprecip())
