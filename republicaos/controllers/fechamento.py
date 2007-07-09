# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone, Fechamento
from datetime          import date
from dateutil.relativedelta import relativedelta
from republicaos.utils.flash import flash_errors, flash
import cherrypy



class FechamentoController(controllers.Controller):
	@expose(template = 'republicaos.templates.fechamento')
	@error_handler()
	@validate(validators = dict(data_fechamento = validators.DateConverter(month_style='dd-mm-yyyy')))
	def default(self, data_fechamento = None, tg_errors = None):
		if tg_errors:
			raise redirect('/')
		republica = Republica.get_by(id = 1)
		
		if not data_fechamento or \
			 data_fechamento > date.today() or \
			 data_fechamento <= republica.data_criacao:
			data_fechamento = date.today()
		
		fechamento = republica.fechamento_na_data(data_fechamento - relativedelta(days = 1))
		if not fechamento:
			republica.criar_fechamento()
			fechamento = republica.fechamentos[0]
		fechamento.executar_rateio()
		cherrypy.session['fechamento'] = fechamento
		
		return dict(fechamento = fechamento)