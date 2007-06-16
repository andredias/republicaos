# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone, Fechamento
from datetime          import date
from dateutil.relativedelta import relativedelta
from republicaos.utils.flash import flash_errors, flash


class FechamentoController(controllers.Controller):
	@expose(template = "republicaos.templates.fechamentos")
	def index(self):
		republica = Republica.get_by(id = 1)
		hoje = date.today()
		while republica.fechamentos[0].data <= hoje:
			republica.criar_fechamento()
		return dict(republica = republica)
	
	
	@expose(template = 'republicaos.templates.fechamento')
	@error_handler()
	@validate(validators = dict(data_fechamento = validators.DateConverter(month_style='dd-mm-yyyy')))
	def show(self, data_fechamento = None, tg_errors = None):
		if tg_errors:
			raise redirect('/')
		republica = Republica.get_by(id = 1)
		if not data_fechamento:
			data_fechamento = date.today()
		fechamento = republica.fechamento_na_data(data_fechamento - relativedelta(days = 1))
		fechamento.executar_rateio()
		return dict(fechamento = fechamento)
	

