
import dash
from dash import dcc
from dash import html
from dash import dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc

from datetime import date

import control
import viewclasses as vc
import json


textcolor='rgba(210,230,255,255)'

def SetupView(controller,dr):
	""" SetupView - sets up view elements

	Arguments:
		controller {Controller Class} -- Controller for program

	"""

	app=controller.app
#	lo=[html.H2(children='Project')]
	lo=[html.H1('Weather Station',style={'textAlign': 'center'})]
	lo.append(html.Div(' ',style={'margin-bottom': 25}))
#	lo=[]
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					[
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Temperature (F)", className="text-primary"), # 
										dbc.ListGroupItem(html.H1("N/A",id='temp-now',className='text-info'),style={'textAlign': 'center','verticalAlign':'middle'}),
										dbc.Table(html.Tbody([
										html.Tr([
											html.Td(html.H5("Temperature Max (24 hrs)"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='temp-max-24',className='text-primary'),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										html.Tr([
											html.Td(html.H5("Temperature Min (24 hrs)"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='temp-min-24',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										])),
									]
								)
							],

						),
						html.Div(' ',style={'margin-bottom': 25}),
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),
				dbc.Col(
					[
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Humidity (%)", className="text-primary"),
										dbc.ListGroupItem(html.H1("N/A",id='humidity-now',className='text-info'),style={'textAlign': 'center','verticalAlign':'middle'}),
										dbc.Table(html.Tbody([
										html.Tr([
											html.Td(html.H5("Humidity Max (24 hrs)"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='humidity-max-24',className='text-primary'),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										html.Tr([
											html.Td(html.H5("Humidity Min (24 hrs)"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='humidity-min-24',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										])),
									]
								)
							],
						),
						html.Div(' ',style={'margin-bottom': 25}),
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,					
				),
				dbc.Col(
					[
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Precipitation (in)", className="text-primary"),
										dbc.Table(html.Tbody([
										html.Tr([
											html.Td(html.H5("Last Hour"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='precip-1hr',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										html.Tr([												
											html.Td(html.H5("Last 24 hrs"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='precip-24hr',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										html.Tr([
											html.Td(html.H5("YTD"),style={'textAlign': 'center','verticalAlign':'middle'}),
											html.Td(html.H5("N/A",id='precip-ytd',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
										]),
										])),
									]
								)
							],
						),
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),
				dbc.Col(
					[
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Forecast", className="text-primary"),
										dbc.Table(html.Tbody([
										html.Tr([
											html.Td(html.H5("N/A",id='forecast',className="text-body"),style={'textAlign': 'left','verticalAlign':'middle'}),
										]),
										html.Tr([
											html.Td(html.H5("N/A",id='forecast-1',className="text-body"),style={'textAlign': 'left','verticalAlign':'middle'}),
										]),
										])),
									]
								),
							],
						),
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),

			],
			justify='center',
		)
	)
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					[
						dcc.Graph(id=vc.theSpeedGauge.id,config={'staticPlot':True}), 
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Wind Speed (MPH)", className="text-primary"),
										dbc.Table(html.Tbody([
											html.Tr([
												html.Td(html.H5("Ave (1m)"),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H4("N/A",id='wind_vmph-1m',className='text-primary'),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H5("  ",id='empty',className="text-primary"),style={'textAlign': 'center'}),
											]),
											html.Tr([													
												html.Td(html.H5("Max (24 hrs)"),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H4("N/A",id='wind_vmph-max',className='text-primary'),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H5("Now",id='wind_vmph-max-time',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
											]),
											html.Tr([
												html.Td(html.H5("Record"),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H4("N/A",id='wind_vmph-record',className='text-primary'),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H5("Now",id='wind_vmph-record-time',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
											]),
										])),		
									]
								),
							]
						),
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),
				dbc.Col(
					[
						dcc.Graph(id=vc.theAngleGauge.id,config={'staticPlot':True}),
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Wind Angle", className="text-primary"),
										dbc.Table(html.Tbody([
											html.Tr([
												html.Td(html.H5("Average (1 min)"),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H4("N",id='wind_angle-1m',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
											]),
											html.Tr([
												html.Td(html.H5("Median (24 hrs)"),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H4("N",id='wind_angle-24',className="text-primary"),style={'textAlign': 'center','verticalAlign':'middle'}),
											]),
											])),
									]),
							],
						),
						html.Div(' ',style={'margin-bottom': 25}),
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Status", className="text-primary"),										
										dbc.Table(html.Tbody([
											html.Tr([
												html.Td(html.H5("Last Update "),style={'textAlign': 'center','verticalAlign':'middle'}),
												html.Td(html.H5("Now ",id='wind_angle-lastupdate',className="text-success"),style={'textAlign': 'center','verticalAlign':'middle'}),
											]),
										])),
									],
								),
							],
						),	
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),
			],
			justify='center',
		)
	)

	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Graph(id=vc.theDataGraph.id)
			)
		)
	)
	
	lo.append(
		dbc.Row(
			dbc.Col(
				html.Div(' ',style={'margin-bottom': 25})
			)
		)
	)
	
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					[
						html.H4('From Date'),
						dcc.DatePickerSingle(
								 id='plot-date-picker',
								 min_date_allowed=date(2022, 2, 9),
#								 max_date_allowed=date(2017, 9, 19),
								 initial_visible_month=date.today(),
								 date=date.today(),
								 className='dark-theme-control'
						)
					],
#					width=4,
				),
				dbc.Col(
					html.Div(
						[
							html.H4('Plot for (days)'),
							dbc.RadioItems(	
								id="radio-plot-span",
								className="btn-group",
								inputClassName="btn-check",
								labelClassName="btn btn-outline-primary btn-lg",
								labelCheckedClassName="active",
								options=[
									{"label": "1", "value": 24},
									{"label": "3", "value": 72},
									{"label": "7", "value": 7*24},
								],
								value=24,
							)
						],
	#					width=4,
						className='radio-group',
					)	
				),
				dbc.Col(
					html.Div(
						[
							html.H4('Plot by'),
							dbc.RadioItems(	
								id="radio-plot-grain",
								className="btn-group",
								inputClassName="btn-check",
								labelClassName="btn btn-outline-primary btn-lg",
								labelCheckedClassName="active",
								options=[
									{"label": "Hourly", "value": 'hourly'},
									{"label": "Daily", "value": 'daily'},
									{"label": "Points", "value": 'points'},
								],
								value='hourly',
							)
						],
	#					width=4,
						className='radio-group',
					)
				)
			],
#			justify='center',
		)
	)
	
	lo.append(
		dbc.Row(
			dbc.Col(
				html.Div(' ',style={'margin-bottom': 25})
			)
		)
	)
	
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					dbc.Collapse(
						dcc.Checklist(
							options=[{'label':v,'value':v} for v in dr.data_cache.keys()],
							value=['wind_vmph'],
							inputClassName='form-check-input',
							labelStyle = dict(display='block',className='form-check-label'),
							id=vc.theYColumnPicker.id
						),
						id="collapse",
						is_open=False,
						className='form-check',
					),
				),
			],
		)
	)

	lo.append(
		dbc.Row(
			[
				dbc.Col(
					dbc.Button(
						"Available Data",
						id="collapse-button",
						outline=True,
						class_name='btn btn-outline-primary btn-lg',
						n_clicks=0,
					),
				),
			]
		)
	)
	
	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Interval(interval=vc.theStatsInterval.interval,id=vc.theStatsInterval.id,n_intervals=0)
			)
		)
	)

	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Interval(interval=vc.theInterval.interval,id=vc.theInterval.id,n_intervals=0)
			)
		)
	)

	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Interval(interval=vc.theForecastInterval.interval,id=vc.theForecastInterval.id,n_intervals=0)
			)
		)
	)


	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Interval(interval=vc.theDailyPrecipInterval.interval,id=vc.theDailyPrecipInterval.id,n_intervals=0)
			)
		)
	)


	
	
	#	lo.append(html.Div(id=vc.theLocalData.id,children=df.to_json(orient='split'),style={'display': 'none'}))
	lo.append(
		dbc.Row(
			[
				html.Div(id=vc.theLocalGranularityState.id,style={'display': 'none'},children=json.dumps({'granularity':'plot-button-points'})),
				html.Div(id=vc.theLocalTimeSpanState.id,style={'display': 'none'},children=json.dumps({'timespan':'plot-button-24'}))
			]
		)
	)

#	rc=[dbc.Row(lo)]
	
	app.layout=html.Div(children=lo)
