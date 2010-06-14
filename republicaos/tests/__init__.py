# -*- coding: utf-8 -*-
"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.
"""

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
from pylons import url
from routes.util import URLGenerator
from webtest import TestApp

import pylons.test
from elixir import *
from republicaos.model import *
from republicaos import model as model
from sqlalchemy import engine_from_config

__all__ = ['environ', 'url', 'TestController', 'TestModel',
           'TestAuthenticatedController', 'TestProtectedAreasController']


# Invoke websetup with the current config file
SetupCommand('setup-app').run([pylons.test.pylonsapp.config['__file__']])


# additional imports ...
import os
import logging
from paste.deploy import appconfig
from republicaos.config.environment import load_environment

log = logging.getLogger(__name__)
here_dir = os.path.dirname(__file__)
conf_dir = os.path.dirname(os.path.dirname(here_dir))

test_file = os.path.join(conf_dir, 'test.ini')
conf = appconfig('config:' + test_file)
config = load_environment(conf.global_conf, conf.local_conf)
environ = {}

engine = engine_from_config(config, 'sqlalchemy.')
model.init_model(engine)
metadata = elixir.metadata
Session = elixir.session = meta.Session


# veja http://blog.ianbicking.org/illusive-setdefaultencoding.html
# estava dando uns erros na hora de imprimir mensagens de erro na tela pelo unittest.py
# o remendo abaixo deve poder ser excluído com o Pyhton 3.x, eu espero
import sys
reload(sys)
sys.setdefaultencoding('utf8')




class Individual(Entity):
    """Table 'Individual'.

    >>> me = Individual('Groucho')

    # 'name' field is converted to lowercase
    >>> me.name
    'groucho'
    """
    name = Field(String(20), unique=True)
    favorite_color = Field(String(20))

    def __init__(self, name, favorite_color=None):
        self.name = str(name).lower()
        self.favorite_color = favorite_color

setup_all()

def setup():
    pass

def teardown():
    pass

class TestModel(object):
    def setUp(self):
        setup_all(True)

    def tearDown(self):
        drop_all()
        Session.expunge_all()


class TestController(TestModel):
    def setUp(self):
        TestModel.setUp(self)
        self.app.reset()

    def __init__(self, *args, **kwargs):
        wsgiapp = pylons.test.pylonsapp
        config = wsgiapp.config
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
    

class TestAuthenticatedController(TestModel):

    def __init__(self, *args, **kwargs):
        wsgiapp = pylons.test.pylonsapp
        config = wsgiapp.config
        self.app = TestApp(wsgiapp, extra_environ=dict(REMOTE_USER='admin'))
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestModel.__init__(self, *args, **kwargs)



class TestProtectedAreasController(TestModel):
    """Enable the skip_authentication facility, allow access"""
    def __init__(self, *args, **kwargs):
        wsgiapp = loadapp('config:%s#main_without_authn' % config['__file__'])
        config = wsgiapp.config
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestModel.__init__(self, *args, **kwargs)

