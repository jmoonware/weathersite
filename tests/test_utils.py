
import sys
sys.path.append("..")
import utils

def test_update_forecast():
	fc_strings = utils.update_forecast();
	assert len(fc_strings) > 0
	for i in range(len(fc_strings)):
		print(fc_strings[i])
		assert len(fc_strings[i]) > 0
	
