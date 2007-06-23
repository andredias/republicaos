# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone
from datetime          import date
from decimal           import Decimal
from elixir            import objectstore


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
		objectstore.clear()
		conta_telefone = ContaTelefone.get_by(id = id_conta_telefone)
		conta_telefone.executar_rateio()
		return dict(conta_telefone = conta_telefone)
	
	
	@expose()
	@error_handler(update)
	@validate(validators = ContaTelefoneSchema())
	def do_update(self, **dados):
		# sem a linha abaixo, o objeto da conta de telefone volta todo alterado por edições anteriores
		# é necessário montar um projeto para mandar para a lista de discussão sobre o tema
		# objectstore.clear()
		conta_telefone = ContaTelefone.get_by(id = dados['id_conta_telefone'])
		conta_telefone.telefone     = dados['telefone']
		conta_telefone.franquia     = Decimal(str(dados['franquia'])) if dados['franquia'] else Decimal(0)
		conta_telefone.servicos     = Decimal(str(dados['servicos'])) if dados['servicos'] else Decimal(0)
		conta_telefone.id_operadora = dados['id_operadora']
		conta_telefone.emissao      = dados['emissao']
		conta_telefone.vencimento   = dados['vencimento']
		conta_telefone.flush()
		
		#print '\n\n'
		#for telefonema in conta_telefone.telefonemas:
			#print telefonema.numero, telefonema.responsavel.pessoa.nome if telefonema.responsavel else None
		#print '\n\n'
		
		to_int    = validators.Int().to_python
		republica = Republica.get_by(id = 1)
		for idx in range(len(dados['numero'])):
			old_id_responsavel = to_int(dados['old_id_responsavel'][idx])
			id_responsavel     = to_int(dados['id_responsavel'][idx])
			if old_id_responsavel != id_responsavel:
				numero      = to_int(dados['numero'][idx])
				responsavel = Morador.get_by(id = id_responsavel) if id_responsavel else None
				telefonema  = conta_telefone.telefonema(numero)
				telefonema.responsavel = responsavel
				telefonema.flush()
				republica.registrar_responsavel_telefone(numero = numero, responsavel = responsavel)
		
		raise redirect('/conta_telefone/update/%d' % conta_telefone.id)
