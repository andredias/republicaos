# -*- coding: utf-8 -*-

# inspirado em http://www.nabble.com/My-turbogears.flash()-alternative-t3896614.html

import cherrypy
import genshi

class FlashMessage(object):
	def __init__(self, message, message_type):
		self.message      = message
		self.message_type = message_type
	
	def __repr__(self):
		return self.message
	
	@property
	def attrs(self):
		return {'class': '.%s' % self.message_type}
	
	def to_genshi(self):
		return genshi.Markup(self.message)


class FlashMessagesIterator(object):
	def __init__(self):
		self.messages = list()
	
	def append(self, message):
		self.messages.append(message)
	
	def __iter__(self):
		return self
	
	def next(self):
		if len(self.messages):
			return self.messages.pop(0)
		else:
			raise StopIteration


def flash(message, message_type = 'ok'):
	if 'flash' not in cherrypy.session:
		cherrypy.session['flash'] = FlashMessagesIterator()
		
	flash_message = FlashMessage(message, message_type)
	cherrypy.session['flash'].append(flash_message)


def flash_errors(tg_errors):
	for field, error in tg_errors.items():
		message = '%s: %s' % (field, error)
		flash(message = message, message_type = 'error')
