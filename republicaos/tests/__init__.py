"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.
"""
from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
from pylons import config, url
from routes.util import URLGenerator
from webtest import TestApp

import pylons.test
from elixir import *
from republicaos.model import *
from republicaos.model import meta
from republicaos import model as model
from sqlalchemy import engine_from_config

__all__ = ['environ', 'url', 'TestController', 'TestModel', 
           'TestAuthenticatedController', 'TestProtectedAreasController']


# Invoke websetup with the current config file
# SetupCommand('setup-app').run([config['__file__']])

# additional imports ...
import os
from paste.deploy import appconfig
from republicaos.config.environment import load_environment

here_dir = os.path.dirname(__file__)
conf_dir = os.path.dirname(os.path.dirname(here_dir))

test_file = os.path.join(conf_dir, 'test.ini')
conf = appconfig('config:' + test_file)
load_environment(conf.global_conf, conf.local_conf)
environ = {}

engine = engine_from_config(config, 'sqlalchemy.')
model.init_model(engine)
metadata = elixir.metadata
Session = elixir.session = meta.Session

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

class TestModel(TestCase):
    def setUp(self):
        setup_all(True)
    
    def tearDown(self):
        drop_all(engine)
        Session.expunge_all()



#    def setUp(self):
#        import datetime
#        import hashlib
#        metadata.create_all()
#        gadmin = model.user.Group(
#                name = u"Administrators",
#                description = u"Administration group",
#                created = datetime.datetime.utcnow(),
#                active = True)
#        Session.add(gadmin)
#        g = model.Session.query(
#                model.user.Group).filter_by(
#                    name=u"Administrators").all()
#        # assert len(g) == 1
#        # assert g[0] == gadmin
#        admin = model.user.User(
#                    username = u"admin", 
#                    password=hashlib.sha1("admin").hexdigest(),
#                    password_check=hashlib.sha1("admin").hexdigest(), 
#                    email="admin@example.com",
#                    created = datetime.datetime.utcnow(),
#                    active = True)
#        Session.add(admin)
#        gadmin.users.append(admin)
#        Session.commit()
#        # Check the status
#        u = Session.query(
#                model.user.User).filter_by(
#                    username=u"admin").all()
#        assert len(u) == 1
#        assert u[0] == admin
#        self.user = model.user.User(username = u'tester', 
#                               password = hashlib.sha1('test').hexdigest(), 
#                               password_check = hashlib.sha1('test').hexdigest(), 
#                               created = datetime.datetime.utcnow(),
#                               email = 'test@here.com',
#                               active=True)
#        Session.add(self.user)
#        u2 = Session.query(
#                model.user.User).filter_by(
#                    username=u"tester").all()
#        assert len(u2) == 1
#        assert u2[0] == self.user
#        self.ngroup = model.user.Group(name = u'Subscription Members',
#                                       created = datetime.datetime.utcnow())
#        self.ngroup.permissions.append(model.user.Permission(name = u'add_users'))
#        Session.add(self.ngroup)
#        Session.commit()
#    
#    
#    def tearDown(self):
#        Session.rollback()
#        model.metadata.drop_all(engine)
#        Session.close()


class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestCase.__init__(self, *args, **kwargs)


class TestAuthenticatedController(TestModel):
    
    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        self.app = TestApp(wsgiapp, extra_environ=dict(REMOTE_USER='admin'))
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestCase.__init__(self, *args, **kwargs)
    


class TestProtectedAreasController(TestModel):
    """Enable the skip_authentication facility, allow access"""
    def __init__(self, *args, **kwargs):
        wsgiapp = loadapp('config:%s#main_without_authn' % config['__file__'])
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestCase.__init__(self, *args, **kwargs)
    
