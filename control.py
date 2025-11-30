import dash
import dash_bootstrap_components as dbc
import flask

class Controller():
	def __init__(self,debug=True,host='127.0.0.1',port=8050):
		self.debug=debug
		self.server=flask.Flask(__name__)
		self.app=dash.Dash(__name__,server=self.server,
			external_stylesheets=[dbc.themes.CYBORG],
			meta_tags=[{'name':'viewport','content':'width=device-width, initial-scale=1'}]
		)
		import callbacks
		callbacks.SetupCallbacks(self.app)
		self.host=host
		self.port=port
	def Start(self):
		""" params: None """
		self.app.run(debug=self.debug,host=self.host,port=self.port)	
		
