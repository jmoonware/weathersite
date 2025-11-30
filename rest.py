
from flask import Flask, request, jsonify
import data
import logging
import callbacks

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
			return jsonify(data.theDataReader.GetLatestReadings() | data.theDataReader.ephemera)
