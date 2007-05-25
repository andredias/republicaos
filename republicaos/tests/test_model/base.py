#!/usr/bin/python
# -*- coding: utf-8 -*-

from republicaos.model import *
from elixir import *

#def setup():
	#metadata.connect('sqlite:///')
	#metadata.engine.echo = True
	#metadata.create_all()


#def teardown():
	#cleanup_all()


class BaseTest(object):
	url = 'sqlite:///'
	def setup(self):
		metadata.connect(self.url)
		#metadata.connect('sqlite:///')
		#metadata.engine.echo = True
		create_all()
		
	
	def teardown(self):
		# we don't use cleanup_all because setup and teardown are called for 
		# each test, and since the class is not redefined, it will not be
		# reinitialized so we can't kill it
		drop_all()
		objectstore.clear()