
class Origins:
	def __init__(self):
		self.wind_speed='wind_vmph'
		self.wind_angle='wind_angle'
		self.garage_T='garage_T'
		self.garage_H='garage_H'
		self.garage_P='garage_P'

data_root=r'tests/wsdata'
log_path=r'tests/test_log.txt'
# forecast_url = r'https://forecast.weather.gov/MapClick.php?lon=-117.17124938964842&lat=33.03779481374889'
forecast_url = r'https://forecast.weather.gov/MapClick.php?lat=41.9489&lon=-76.7955'
precip_url = r'https://www.wrh.noaa.gov/sgx/obs/rtp/rtp_SGX_{0:02d}'
# https://dex.cocorahs.org/stations/NY-CM-30/obs-tables
page_banner="Weather - Doty Hill"
page_sub_banner="Harvest Lane"
origins = Origins()
report_timezone="US/Eastern"

