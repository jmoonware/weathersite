
class Origins:
	def __init__(self):
		self.wind_speed='wind_vmph'
		self.wind_angle='wind_angle'
		self.outside_T='outside_T'
		self.outside_H='outside_H'
		self.outside_P='outside_P'

data_root=r'/home/jmoon/test/data'
log_path=r'/home/jmoon/test/test_log.txt'
forecast_url = r'https://forecast.weather.gov/MapClick.php?lon=-117.17124938964842&lat=33.03779481374889'
precip_url = r'https://www.wrh.noaa.gov/sgx/obs/rtp/rtp_SGX_{0:02d}'
# https://dex.cocorahs.org/stations/NY-CM-30/obs-tables
page_banner="Weather - Doty Hill"
page_sub_banner="Harvest Lane"
origins = Origins()

