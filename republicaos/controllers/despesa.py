# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, TipoDespesa, Despesa, DespesaPeriodica
from datetime          import date
from decimal           import Decimal


class DespesaSchema(validators.Schema):
	data_vencimento = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	data_termino    = validators.DateConverter(month_style = 'dd/mm/yyyy')
	quantia         = validators.Number(not_empty = True)
	id_tipo_despesa = validators.Int(not_empty = True)
	id_morador      = validators.Int(not_empty = True)
	id_despesa      = validators.Int()



class DespesaController(controllers.Controller):
	@expose()
	def index(self):
		raise redirect('/')
	
	@expose(template = "republicaos.templates.despesa")
	@validate(validators = dict(
		acao = validators.OneOf(['insert', 'update', 'delete']),
		id_despesa = validators.Int() # pode ser vazio
		))
	def default(self, acao, id_despesa = None):
		republica = Republica.get_by(id = 1)
		moradores = Morador.select(Morador.c.id_republica == 1)
		
		if acao != 'insert' and not id_despesa:
			flash('Página não encontrada')
			raise redirect('/')
		elif acao == 'delete':
			despesa = Despesa.get_by(id = id_despesa)
			despesa.delete()
			despesa.flush()
			raise redirect('/')
		elif acao == 'insert':
			despesa = Despesa(
				data        = date.today(),
				republica   = republica,
				responsavel = moradores[0],
				tipo        = republica.tipos_despesa[0]
				)
		elif acao == 'update':
			despesa = Despesa.get_by(id = id_despesa)
			
		dados = dict()
		
		dados['moradores'] = moradores
		dados['republica'] = republica
		dados['despesa']   = despesa
		dados['acao']      = acao
		return dados
	
	@expose()
	@error_handler(index)
	@validate(validators = DespesaSchema())
	def cadastrar_despesa(self, **dados):
		republica    = Republica.get_by(id = 1)
		tipo_despesa = TipoDespesa.get_by(id = dados['id_tipo_despesa'], republica = republica)
		morador      = Morador.get_by(id = dados['id_morador'])
		if 'periodicidade' not in dados:
			despesa = Despesa.get_by(id = dados['id_despesa']) if dados['id_despesa'] else Despesa()
			despesa.data = dados['data_vencimento']
		else:
			despesa = DespesaPeriodica.get_by(id = dados['id_despesa']) if dados['id_despesa'] else DespesaPeriodica()
			despesa.proximo_vencimento = dados['data_vencimento']
			despesa.data_termino       = dados['data_termino']
			
		despesa.quantia     = Decimal(str(dados['quantia']))
		despesa.tipo        = tipo_despesa
		despesa.responsavel = morador
		
		despesa.flush()
		flash('Despesa cadastrada com sucesso!')
		raise redirect('/despesa/insert/')
	
