# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, TipoDespesa, Despesa, DespesaPeriodica
from datetime          import date


class DespesaSchema(validators.Schema):
	data_vencimento = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	data_termino    = validators.DateConverter(month_style = 'dd/mm/yyyy')
	quantia         = validators.Number(not_empty = True)
	id_tipo_despesa = validators.Int(not_empty = True)
	id_morador      = validators.Int(not_empty = True)



class DespesaController(controllers.Controller):
	@expose(template = "republicaos.templates.despesa")
	def index(self, **dados):
		republica = Republica.get_by(id = 1)
		moradores = Morador.select(Morador.c.id_republica == 1)
		if not dados:
			dados = dict()
		
		dados['hoje'] = date.today()
		dados['moradores'] = moradores
		dados['republica'] = republica
		return dados
	
	@expose()
	@error_handler(index)
	@validate(validators = DespesaSchema())
	def cadastrar_despesa(self, **dados):
		republica    = Republica.get_by(id = 1)
		tipo_despesa = TipoDespesa.get_by(id = dados['id_tipo_despesa'], republica = republica)
		morador      = Morador.get_by(id = dados['id_morador'])
		if dados['periodicidade'] == 'uma_vez':
			despesa = Despesa(
						data        = dados['data_vencimento'],
						quantia     = dados['quantia'],
						tipo        = tipo_despesa,
						responsavel = morador
						)
		else:
			despesa = DespesaPeriodica(
						proximo_vencimento = dados['data_vencimento'],
						quantia            = dados['quantia'],
						tipo               = tipo_despesa,
						responsavel        = morador,
						data_termino       = dados['data_termino']
						)
		despesa.flush()
		raise redirect('/despesa')
	
