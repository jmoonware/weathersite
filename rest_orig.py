
from flask_restful import reqparse, abort, Api, Resource
import data
import logging

api = None 

def abort_if_sensor_doesnt_exist(sensor_id):
    if sensor_id not in data.LatestSensorData:
        abort(404, message="sensor {} doesn't exist".format(sensor_id))

# apparently reqparse is deprecated
# make sure to use Flask/Werzeug 2.0.2 or earlier! v. 2.2.2 breaks this interface!
parser = reqparse.RequestParser()
parser.add_argument('time')
parser.add_argument('reading')

# sensor
# shows a single sensor item and lets you delete a sensor item
class Sensor(Resource):
#    def get(self, sensor_id):
#        abort_if_sensor_doesnt_exist(sensor_id)
#        return data.LatestSensorData[sensor_id]

#	def delete(self, sensor_id):
#		abort_if_sensor_doesnt_exist(sensor_id)
#		del data.LatestSensorData[sensor_id]
#		return '', 204
	
	def get(self, sensor_id):
		args = parser.parse_args()
		new_reading = None

		if args['time'] and args['reading']:
			try:
				float_read=float(args['reading'])
				float_time=float(args['time'])
				new_reading = {'time': float_time,'reading': float_read}
				data.theDataWriter.LogData(sensor_id,float_read,timestamp=float_time)
			except ValueError:
				logging.getLogger(__name__).debug("REST Value Error {0} got args {1}".format(sensor_id,args))
			except Exception as ex:
				logging.getLogger(__name__).debug("REST unhandled {0}".format(sensor_id,ex))
		return new_reading, 201


# SensorList endpoint
# shows a list of all sensor data
class SensorList(Resource):
	def get(self):
		return data.theDataReader.GetLatestReadings()

##
## Actually setup the Api resource routing here
##
def SetupRest(server):
	api=Api(server)
	api.add_resource(SensorList, '/sensors')
	api.add_resource(Sensor, '/sensors/<sensor_id>')
