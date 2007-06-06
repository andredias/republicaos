# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone
from datetime          import date
from decimal           import Decimal


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
		republica = Republica.get_by(id = 1)
		conta     = ContaTelefone.get_by(id = id_conta_telefone)
		conta.delete()
		conta.flush()
		raise redirect('/')
	
	
	@expose(template = "republicaos.templates.conta_telefone_insert")
	def insert(self):
		return dict()
		
		
	@expose()
	@error_handler(insert)
	@validate(validators = ContaTelefoneSchema())
	def do_insert(self, **dados):
		republica = Republica.get_by(id = 1)
		
		# verificar como fazer o controle de transação
		conta_telefone = ContaTelefone(
			republica    = republica,
			telefone     = dados['telefone'],
			franquia     = dados['franquia'],
			servicos     = dados['servicos'],
			id_operadora = dados['id_operadora'],
			emissao      = dados['emissao'],
			vencimento   = dados['vencimento']
			)
		conta_telefone.flush()
		conta_telefone.importar_csv(dados['csv'].encode('utf-8'))
		
		raise redirect('/conta_telefone/update/%d' % conta_telefone.id)
	
	
	@expose(template = 'republicaos.templates.conta_telefone_update')
	@error_handler()
	@validate(validators = dict(id_conta_telefone = validators.Int(not_empty = True)))
	def update(self, id_conta_telefone):
		conta_telefone = ContaTelefone.get_by(id = id_conta_telefone)
		conta_telefone.executar_rateio()
		return dict(conta_telefone = conta_telefone)
	
	
	@expose()
	@error_handler(update)
	@validate(validators = ContaTelefoneSchema())
	def do_update(self, **dados):
		conta_telefone = ContaTelefone.get_by(id = dados['id_conta_telefone'])
		conta_telefone.telefone     = dados['telefone']
		conta_telefone.franquia     = Decimal(str(dados['franquia']))
		conta_telefone.servicos     = Decimal(str(dados['servicos']))
		conta_telefone.id_operadora = dados['id_operadora']
		conta_telefone.emissao      = dados['emissao']
		conta_telefone.vencimento   = dados['vencimento']
		conta_telefone.flush()
		
		to_int       = validators.Int().to_python
		telefonemas  = dict([(telefonema.numero, telefonema) for telefonema in conta_telefone.telefonemas])
		republica    = Republica.get_by(id = 1)
		numeros      = [to_int(numero) for numero in dados['numero']]
		responsaveis = [Morador.get_by(id = to_int(id_responsavel)) for id_responsavel in dados['id_responsavel']]
		
		for idx in range(len(numeros)):
			numero      = numeros[idx]
			responsavel = responsaveis[idx]
			telefonemas[numero].responsavel = responsavel
			telefonemas[numero].flush()
			republica.registrar_responsavel_telefone(numero = numero, responsavel = responsavel)
		
		raise redirect('/conta_telefone/update/%d' % conta_telefone.id)
