# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone
from datetime          import date
from decimal           import Decimal
from elixir            import session
from republicaos.utils.flash import flash_errors, flash

import cherrypy


class ContaTelefoneSchema(validators.Schema):
	emissao       = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	vencimento    = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	franquia      = validators.Number(not_empty = True)
	servicos      = validators.Number()
	id_operadora  = validators.Int(not_empty = True)
	telefone      = validators.Int(not_empty = True)



class ContaTelefoneController(controllers.Controller):
	@expose()
	def index(self):
		raise redirect('/conta_telefone/insert/')
	
	@expose()
	@validate(validators = dict(id_conta_telefone = validators.Int(not_empty = True)))
	def delete(self, id_conta_telefone):
		conta = ContaTelefone.get_by(id = id_conta_telefone)
		# assert conta.republica is morador.republica
		conta.delete()
		conta.flush()
		raise redirect('/')
	
	@validate(validators = ContaTelefoneSchema())
	def valida_conta(self, tg_errors = None, **kwargs):
		fechamento = cherrypy.session['fechamento']
		if not tg_errors:
			tg_errors = dict()
		
		if not (fechamento.data_inicial <= kwargs['emissao'] <= fechamento.data_final):
			tg_errors['Data de emissao'] = u'Data da emissão da conta fora da data do fechamento (%s, %s)' % \
				(fechamento.data_inicial.strftime('%d/%m/%Y'), fechamento.data_final.strftime('%d/%m/%Y'))
		
		if (kwargs['vencimento'] < kwargs['emissao']):
			tg_errors['Data do vencimento'] = u'Data do vencimento anterior à data da emissão'
			
		return (tg_errors, kwargs)
	
	
	def do_cadastro_conta(self, dados):
		republica = cherrypy.session['republica']
		
		# verificar como fazer o controle de transação
		if 'id_conta_telefone' in dados:
			conta_telefone = ContaTelefone.get_by(id = dados['id_conta_telefone'])
		else:
			conta_telefone = ContaTelefone(republica = republica)
		
		conta_telefone.telefone     = dados['telefone']
		conta_telefone.franquia     = Decimal(str(dados['franquia'])) if dados['franquia'] else Decimal(0)
		conta_telefone.servicos     = Decimal(str(dados['servicos'])) if dados['servicos'] else Decimal(0)
		conta_telefone.id_operadora = dados['id_operadora']
		conta_telefone.emissao      = dados['emissao']
		conta_telefone.vencimento   = dados['vencimento']
		conta_telefone.flush()
		
		if 'numero' in dados:
			#print '\n\n'
			#for telefonema in conta_telefone.telefonemas:
				#print telefonema.numero, telefonema.responsavel.pessoa.nome if telefonema.responsavel else None
			#print '\n\n'
			
			to_int = validators.Int().to_python
			for idx in xrange(len(dados['numero'])):
				old_id_responsavel = to_int(dados['old_id_responsavel'][idx])
				id_responsavel     = to_int(dados['id_responsavel'][idx])
				if old_id_responsavel != id_responsavel:
					numero      = to_int(dados['numero'][idx])
					responsavel = Morador.get_by(id = id_responsavel) if id_responsavel else None
					telefonema  = conta_telefone.telefonema(numero)
					telefonema.responsavel = responsavel
					telefonema.flush()
					republica.registrar_responsavel_telefone(numero = numero, responsavel = responsavel)
		else: # 'csv' in dados
			try:
				conta_telefone.importar_csv(dados['csv'].encode('utf-8'))
			except Exception:
				#TODO: fazer algum tratamento de exceção aqui
				pass
		
		raise redirect('/conta_telefone/update/%d' % conta_telefone.id)
	
	
	@expose(template = "republicaos.templates.conta_telefone_insert")
	def insert(self, **kwargs):
		if kwargs:
			tg_errors, kwargs = self.valida_conta(**kwargs)
			if tg_errors:
				flash_errors(tg_errors)
			else:
				self.do_cadastro_conta(kwargs)
		else:
			kwargs['telefone'] = kwargs['emissao'] = kwargs['vencimento'] = kwargs['franquia'] = kwargs['servicos'] = kwargs['csv'] =None
				
		return dict(kwargs)
		
		
	
	@expose(template = 'republicaos.templates.conta_telefone_update')
	@error_handler()
	@validate(validators = dict(id_conta_telefone = validators.Int(not_empty = True)))
	def update(self, id_conta_telefone, **kwargs):
		#session.clear()
		if kwargs:
			tg_errors, kwargs = self.valida_conta(**kwargs)
			if tg_errors:
				flash_errors(tg_errors)
			else:
				kwargs['id_conta_telefone'] = id_conta_telefone
				self.do_cadastro_conta(kwargs)
			
		conta_telefone = ContaTelefone.get_by(id = id_conta_telefone)
		conta_telefone.executar_rateio()
		kwargs['conta_telefone'] = conta_telefone
		return dict(kwargs)
