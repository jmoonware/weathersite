import sys
sys.path.insert(0,'/var/www/project')
sys.path.append('/opt/miniconda3/www-env')
sys.stdout=sys.stderr
from project import server as application
