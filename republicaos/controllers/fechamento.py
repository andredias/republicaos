# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone, Fechamento


class FechamentoController(controllers.Controller):
	@expose(template = "republicaos.templates.fechamentos")
	def fechamentos(self):
		republica = Republica.get_by(id = 1)
		return dict(republica = republica)
	
	
	@expose(template = 'republicaos.templates.fechamento')
	@validate(validators = dict(
		id_republica = validators.Int(),
		data_fechamento = validators.DateConverter(month_style='dd-mm-yyyy'))
	)
	def fechamento(self, id_republica, data_fechamento):
		republica = Republica.get_by(id = id_republica)
		if data_fechamento == republica.proxima_data_fechamento:
			fechamento = Fechamento(data = data_fechamento, republica = republica)
		else:
			fechamento = None
			for f in republica.fechamentos:
				if data_fechamento == f.data:
					fechamento = f
					break
			
		if not fechamento:
			# fechamento não encontrado
			pass
			
		return dict(data_fechamento = type(data_fechamento), fechamento = fechamento)
	

