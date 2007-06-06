# -*- coding: utf-8 -*-

from turbogears     import controllers, expose, flash, error_handler
#from turbogears import identity
from turbogears     import redirect, validate, validators
from cherrypy       import request, response
from datetime       import date
# from republicaos import json
import logging
log = logging.getLogger("republicaos.controllers")

from republicaos.controllers.despesa        import DespesaController
from republicaos.controllers.conta_telefone import ContaTelefoneController
from republicaos.controllers.fechamento     import FechamentoController




class Root(controllers.RootController):
	
	despesa        = DespesaController()
	conta_telefone = ContaTelefoneController()
	fechamentos    = FechamentoController()
	
	@expose()
	# @identity.require(identity.in_group("admin"))
	def index(self):
		raise redirect('/fechamentos/show')