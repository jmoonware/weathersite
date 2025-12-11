import sys
sys.path.insert(0,'/var/www/weathersite')
sys.path.append('/var/www/weathersite/.venv')
sys.stdout=sys.stderr
from project import server as application
