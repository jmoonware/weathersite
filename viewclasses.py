import data



class MainGraph():
	def __init__(self,id='main-graph'):
		""" parameters: id = string identifier ('id' for component, 'component_id' in callback) """
		self.id=id
		self.figure='figure'

class TextDiv():
	def __init__(self,id='div-text'):
		""" parameters: id = string identifier ('id' for component, 'component_id' in callback) """
		self.id=id
		self.value='children'
		self.initialvalue=''		

class Button():
	def __init__(self,id='button',text='Blarg'):
		self.id = id
		self.text=text
		self.n_clicks='n_clicks'
		self.initialvalue=0
		self.value='value'

class Gauge():
	def __init__(self,id='gauge',text=''):
		self.id = id
		self.text=text
		self.initialvalue=0
		self.value='value'

class Interval():
	def __init__(self,id='update-interval',interval=2*1000):
		self.id = id
		self.interval=interval # in milliseconds
		self.n_intervals='n_intervals'

class ColumnDropdown():
	def __init__(self,id='column-dropdown'):
		""" parameters: id = string identifier ('id' for component, 'component_id' in callback) """
		self.id=id
		self.value="value"
		self.options="options"
		self.dropdownbutton="dropdown-button"
		self.children="children"

theSpeedGauge=MainGraph(id='speed-gauge')		
theAngleGauge=MainGraph(id='angle-gauge')

theLocalGranularityState=TextDiv(id='gran-data')
theLocalTimeSpanState=TextDiv(id='timespan-data')
theRefreshButton=Button(id='refresh-button',text='Refresh')
theInterval=Interval()
theDataGraph=MainGraph(id='data-graph')
theYColumnPicker=ColumnDropdown(id='y-column-picker')
theYColumnAccordian=ColumnDropdown(id='y-column-accordian')
theStatsInterval=Interval(id='stats-interval',interval=60*1000)
theForecastInterval=Interval(id='forecast-interval',interval=30*60*1000)
theDailyPrecipInterval=Interval(id='dailyprecip-interval',interval=60*1000) # 6*60*60*1000)