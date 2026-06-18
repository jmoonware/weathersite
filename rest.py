
from flask import Flask, request, jsonify
import data
import logging
import callbacks
import settings

once = False
def SetupRest(app):
	global once
	if not once:
		once = True

		@app.route('/sensors/<sensor_id>',methods=['GET'])
		def sensor(sensor_id):
			args = request.args
			new_reading = {}
			if args.get('time') and args.get('reading'):
				try:
					float_read=float(args.get('reading'))
					float_time=float(args.get('time'))
					new_reading = {'time': float_time,'reading': float_read}
					data.theDataWriter.LogData(sensor_id,float_read,timestamp=float_time)
				except ValueError:
					logging.getLogger(__name__).debug("REST Value Error {0} got args {1}".format(sensor_id,args))
				except Exception as ex:
					logging.getLogger(__name__).debug("REST unhandled {0}".format(sensor_id,ex))
			return new_reading
		
		# shows a list of all sensor data
		@app.route('/sensors',methods=['GET'])
		def get_latest_sensors():
			return jsonify(data.theDataReader.GetLatestReadings())
		 
		# shows a list of all sensor data
		@app.route('/micro',methods=['GET'])
		def get_latest_all():
			callbacks.update_all()
			readings = data.theDataReader.GetLatestReadings() 
			filtered_readings = {}
			filtered_readings['wind_vmph']=None
			if 'wind_vmph' in readings:
				filtered_readings['wind_vmph']=readings['wind_vmph']
			filtered_readings['wind_angle']=None
			if 'wind_angle' in readings:
				filtered_readings['wind_angle']=readings['wind_angle']
			return jsonify(filtered_readings | data.theDataReader.ephemera)
		# just the forecast, which can be variable size
		@app.route('/microf',methods=['GET'])
		def get_latest_forecast():
			args = request.args
			width = 100
			height = 100
			if args.get('width'):
				width = int(args.get('width'))
			callbacks.update_all()
			forecast_strings = {}
			# collect the forecast strings; probably should be in a 
			# separate dict eventually
			# these can be longer than the screen width so inject line breaks 
			# at the proper places
			# the code on the microcontroller will keep track of the 
			# number of lines
			for key in data.theDataReader.ephemera:
				if 'Forecast' in key:
					forecast_strings[key] = data.theDataReader.ephemera[key]
			# here we fix the text justification based on screen size
			justified_strings = []
			for fsk in forecast_strings:
				toks = forecast_strings[fsk].split(' ')
				justified_strings.append('')
				cline=''
				for itok,tok in enumerate(toks):
					tcline = cline + ' ' + tok
					if len(tcline) < width and itok + 1 != len(toks):
						cline = tcline
					else: # end line here
						if itok + 1 == len(toks):
							justified_strings[-1] = cline + ' ' +  tok
						else:
							justified_strings[-1] = cline 
							cline = tok
						justified_strings.append('')
			return jsonify(justified_strings)
		# just front screen values
		@app.route('/microd',methods=['GET'])
		def get_latest_data():
			args=request.args
			callbacks.update_all()
			readings = data.theDataReader.GetLatestReadings() 
			filtered_readings = {}
			filtered_readings['wind_vmph']=None
			if 'wind_vmph' in readings:
				filtered_readings['wind_vmph']=readings['wind_vmph']
			filtered_readings['wind_angle']=None
			if 'wind_angle' in readings:
				filtered_readings['wind_angle']=readings['wind_angle']
			# if we use 'v' as an arg only return wind speed/angle
			if not args.get('v'):
				for key in data.theDataReader.ephemera:
					if not 'Forecast' in key:
						filtered_readings[key]=data.theDataReader.ephemera[key]
			return jsonify(filtered_readings)
		@app.route('/microh',methods=['GET'])
		def get_latest_history(origin=None):
			if origin==None:
				origin = settings.origins.outside_T
			filtered_readings = {}
			times,readings = data.theDataReader.GetCacheStats(origin,oldest_hour=8,hourly=True)
			filtered_readings['x']=times
			filtered_readings['y']=readings
			return jsonify(filtered_readings)

