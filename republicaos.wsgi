# Add the virtual Python environment site-packages directory to the path
import site
site.addsitedir('/home/andref/projetos/pylons/lib/python2.6/site-packages')

# Avoid ``[Errno 13] Permission denied: '/var/www/.python-eggs'`` messages
import os
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'

# Load the Pylons application
from paste.deploy import loadapp
application = loadapp('config:/home/andref/projetos/pylons/republicaos/development.ini')
