import control
import data
import view
import rest

# use this file as the entry point on an Apache or gunicorn server

theController=control.Controller(debug=False)
data.StartDataLogging()
view.SetupView(theController,data.theDataReader)
rest.SetupRest(theController.server)

# import this server (which is a flask.Flask() server in the wsgi file)
server=theController.server
