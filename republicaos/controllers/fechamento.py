# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone, Fechamento
from datetime          import date


class FechamentoController(controllers.Controller):
	@expose(template = "republicaos.templates.fechamentos")
	def index(self):
		republica = Republica.get_by(id = 1)
		return dict(republica = republica)
	
	
	@expose(template = 'republicaos.templates.fechamento')
	@validate(validators = dict(data_fechamento = validators.DateConverter(month_style='dd-mm-yyyy')))
	def show(self, data_fechamento = None):
		republica = Republica.get_by(id = 1)
		if not data_fechamento or data_fechamento == republica.proxima_data_fechamento:
			fechamento = Fechamento(data = republica.proxima_data_fechamento, republica = republica)
			# TODO: ainda não está claro como registrar o fechamento definitivamente.
			if fechamento.data < date.today():
				fechamento.flush()
		else:
			fechamento = None
			for f in republica.fechamentos:
				if data_fechamento == f.data:
					fechamento = f
					break
			
		if not fechamento:
			# fechamento não encontrado
			flash('Fechamento inexistente')
			raise redirect('/fechamento/fechamentos')
		
		fechamento.executar_rateio()
		return dict(fechamento = fechamento)
	

