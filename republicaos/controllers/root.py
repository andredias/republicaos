# -*- coding: utf-8 -*-

from turbogears     import controllers, expose, flash, error_handler
#from turbogears import identity
from turbogears     import redirect, validate, validators
from cherrypy       import request, response
from datetime       import date
# from republicaos import json
from republicaos.controllers.despesa        import DespesaController
from republicaos.controllers.conta_telefone import ContaTelefoneController
from republicaos.controllers.fechamento     import FechamentoController
from republicaos.model.business             import Republica
import cherrypy
import logging
log = logging.getLogger("republicaos.controllers")




class Root(controllers.RootController):
    
    despesa        = DespesaController()
    conta_telefone = ContaTelefoneController()
    fechamento     = FechamentoController()
    
    @expose()
    # @identity.require(identity.in_group("admin"))
    def index(self):
        cherrypy.session['republica'] = Republica.get_by(id = 1)
        raise redirect('/fechamento/')
