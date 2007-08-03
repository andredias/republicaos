# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, error_handler, redirect, validate, validators, url
from republicaos.model import Republica, Morador, TipoDespesa, Despesa, DespesaPeriodica
from datetime          import date
from decimal           import Decimal
from republicaos.utils.flash import flash_errors, flash

import cherrypy



class DespesaSchema(validators.Schema):
	data_vencimento = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	data_termino    = validators.DateConverter(month_style = 'dd/mm/yyyy')
	quantia         = validators.Number(not_empty = True)
	id_tipo_despesa = validators.Int(not_empty = True)
	id_morador      = validators.Int(not_empty = True)
	#id_despesa      = validators.Int()



class DespesaController(controllers.Controller):
	@expose()
	def index(self):
		raise redirect('/')
	
	
	@expose()
	@validate(validators = dict(id_despesa = validators.Int(not_empty = True)))
	def delete(self, id_despesa):
		despesa = Despesa.get_by(id = id_despesa)
		if not despesa:
			raise cherrypy.NotFound
		despesa.delete()
		despesa.flush()
		flash('Despesa <strong>removida</strong>')
		raise redirect(url('/'))
	
	
	@validate(validators = DespesaSchema())
	def separa_valida_info(self, tg_errors = None, **kwargs):
		# não pode ser chamada por uma rotina que não tenha @expose. Não sei porque
		
		# data_vencimento deve estar dentro do período do fechamento
		if type(kwargs['data_vencimento']) is date:
			fechamento = cherrypy.session['fechamento']
			if not(fechamento.data_inicial <= kwargs['data_vencimento'] <= fechamento.data_final):
				if not tg_errors:
					tg_errors = dict()
				tg_errors['Data Vencimento'] = u'Data do Vencimento deve estar entre %s e %s' % \
								(fechamento.data_inicial.strftime('%d/%m/%Y'), fechamento.data_final.strftime('%d/%m/%Y'))
		
		if ('periodicidade' in kwargs) and (type(kwargs['data_termino']) is date):
			fechamento = cherrypy.session['fechamento']
			if kwargs['data_termino'] < fechamento.data:
				if not tg_errors:
					tg_errors = dict()
				tg_errors[u'Data Término'] = u'Data de término deve ser posterior a %s' % fechamento.data_final.strftime('%d/%m/%Y')
		
		return (tg_errors, kwargs)
	
	
	def doCadastro(self, id_despesa = None, tg_errors = None, **dados):
		if dados:
			if tg_errors:
				flash_errors(tg_errors)
			else:
				# cadastra a despesa
				if 'periodicidade' not in dados:
					despesa      = Despesa() if not id_despesa else Despesa.get_by(id = id_despesa)
					despesa.data = dados['data_vencimento']
				else:
					despesa = DespesaPeriodica() if not id_despesa else DespesaPeriodica.get_by(id = id_despesa)
					despesa.proximo_vencimento = dados['data_vencimento']
					despesa.data_termino       = dados['data_termino']
					
				despesa.tipo        = TipoDespesa.get_by(id = dados['id_tipo_despesa'])
				despesa.responsavel = Morador.get_by(id = dados['id_morador'])
				despesa.quantia     = Decimal(str(dados['quantia']))
				despesa.flush()
				
				# gambiarra para por a despesa periódica na lista do morador
				if type(despesa) is DespesaPeriodica:
					despesa.responsavel.despesas_periodicas.append(despesa)
				
				flash('Despesa <strong>cadastrada</strong>')
				raise redirect(url('/'))
		else:
			if id_despesa:
				# TODO: e se for uma DespesaPeriodica?
				despesa = Despesa.get_by(id = id_despesa)
				if not despesa:
					raise cherrypy.NotFound
			dados['data_vencimento'] = despesa.data           if id_despesa else date.today()
			dados['quantia']         = despesa.quantia        if id_despesa else ''
			dados['id_morador']      = despesa.responsavel.id if id_despesa else None
			dados['id_tipo_despesa'] = despesa.tipo.id        if id_despesa else None
			dados['data_termino']    = despesa.data_termino   if id_despesa and hasattr(despesa, 'data_termino') else None
			dados['periodicidade']   = None
		
		dados['acao'] = url('/despesa/update/%d/' % id_despesa) if id_despesa else url('/despesa/insert')
		return dados
	
	
	@expose(template = "republicaos.templates.despesa")
	def insert(self, **dados):
		tg_errors = None
		if dados:
			tg_errors, dados = self.separa_valida_info(**dados)
		return self.doCadastro(tg_errors = tg_errors, **dados)
	
	
	@expose(template = "republicaos.templates.despesa")
	@validate(validators = dict(id_despesa = validators.Int(not_empty = True)))
	def update(self, id_despesa = None, **dados):
		tg_errors = None
		if dados:
			tg_errors, dados = self.separa_valida_info(**dados)
		return self.doCadastro(id_despesa = id_despesa, tg_errors = tg_errors, **dados)
