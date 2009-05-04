#!/usr/bin/python
# -*- coding: utf-8 -*-

from elixir import metadata, session, setup_all
from republicaos.model.model import *

url = 'sqlite:///:memory:'
#url = 'postgres://turbo_gears:tgears@localhost/tg_teste'
metadata.bind = url
metadata.bind.echo = True
setup_all()

class BaseTest(object):
    def setup(self):
        metadata.create_all()
        #metadata.engine.echo = True
    
    
    def teardown(self):
        # we don't use cleanup_all because setup and teardown are called for
        # each test, and since the class is not redefined, it will not be
        # reinitialized so we can't kill it
        metadata.drop_all()
        session.clear()
