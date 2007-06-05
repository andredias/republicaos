# -*- coding: utf-8 -*-

from turbogears        import controllers, expose, flash, error_handler, redirect, validate, validators
from republicaos.model import Republica, Morador, ContaTelefone
from datetime          import date


class ContaTelefoneSchema(validators.Schema):
	emissao       = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	vencimento    = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
	franquia      = validators.Number(not_empty = True)
	servicos      = validators.Number()
	id_operadora  = validators.Int(not_empty = True)
	telefone      = validators.Int(not_empty = True)
	csv           = validators.NotEmpty()



class ContaTelefoneController(controllers.Controller):
	@expose(template = "republicaos.templates.cadastrar_conta_telefone")
	def index(self):
		return dict(hoje = date.today())
	
	
	@expose()
	@error_handler(index)
	@validate(validators = ContaTelefoneSchema())
	def importar_conta_telefone(self, **dados):
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
		
		raise redirect('/conta_telefone/determinar_responsaveis', id_conta_telefone = conta_telefone.id)
	
	
	@expose(template = 'republicaos.templates.conta_telefone_determinar_responsaveis')
	def determinar_responsaveis(self, **params):
		conta_telefone = ContaTelefone.get_by(id = params['id_conta_telefone'])
		return dict(conta_telefone = conta_telefone)
	
	
	@expose()
	def registrar_responsavel_telefone(self, **dados):
		to_int       = validators.Int().to_python
		conta_telefone = ContaTelefone.get_by(id = to_int(dados['id_conta_telefone']))
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
		
		raise redirect('/conta_telefone')