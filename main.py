# use this file for starting a local server for test
import control
import data
import view
import rest

# entry point
def main():
	theController=control.Controller(debug=True)
	data.StartDataLogging()
	view.SetupView(theController,data.theDataReader)
	rest.SetupRest(theController.server)
	theController.Start()

if __name__=="__main__":
	main()
