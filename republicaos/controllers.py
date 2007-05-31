# -*- coding: utf-8 -*-

from turbogears     import controllers, expose, flash, error_handler
from model.business import *
#from turbogears import identity
from turbogears     import redirect, validate, validators
from cherrypy       import request, response
from datetime       import date
# from republicaos import json
import logging
log = logging.getLogger("republicaos.controllers")


class DespesaSchema(validators.Schema):
	data    = validators.DateConverter(month_style = 'dd/mm/yyyy')
	quantia = validators.Number()
	dia_vencimento  = validators.Int()
	data_termino    = validators.DateConverter(month_style = 'dd/mm/yyyy')
	id_tipo_despesa = validators.Int()

class Root(controllers.RootController):
	@expose(template='.templates.debug')
	def debug(self, **parametros):
		return parametros
	
	
	@expose(template="republicaos.templates.index")
	# @identity.require(identity.in_group("admin"))
	def index(self):
		return dict()
	
	
	@expose(template = "republicaos.templates.despesa")
	@validate(validators = DespesaSchema())
	def despesa(self, **dados):
		republica = Republica.get_by(id = 1)
		moradores = Morador.select(Morador.c.id_republica == 1)
		if not dados:
			dados = dict()
		
		dados['hoje'] = date.today()
		dados['moradores'] = moradores
		dados['republica'] = republica
		return dados
	
	
	@expose()
	@error_handler(despesa)
	@validate(validators = DespesaSchema())
	def cadastrar_despesa(self, **dados):
		republica    = Republica.get_by(id = 1)
		tipo_despesa = TipoDespesa.get_by(id = dados['id_tipo_despesa'], republica = republica)
		morador      = Morador.get_by(id = dados['id_morador'])
		if dados['periodicidade'] == 'uma_vez':
			despesa = Despesa(
						data        = dados['data'],
						quantia     = dados['quantia'],
						tipo        = tipo_despesa,
						responsavel = morador
						)
		else:
			despesa = DespesaPeriodica(
						data_cadastro  = date.today(),
						quantia        = dados['quantia'],
						dia_vencimento = dados['dia_vencimento'],
						tipo           = tipo_despesa,
						responsavel    = morador
						)
		despesa.flush()
		raise redirect('/')
	
	
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
	
	
	#@expose(template="republicaos.templates.login")
	#def login(self, forward_url=None, previous_url=None, *args, **kw):

		#if not identity.current.anonymous \
			#and identity.was_login_attempted() \
			#and not identity.get_identity_errors():
			#raise redirect(forward_url)

		#forward_url=None
		#previous_url= request.path

		#if identity.was_login_attempted():
			#msg=_("The credentials you supplied were not correct or "
				#"did not grant access to this resource.")
		#elif identity.get_identity_errors():
			#msg=_("You must provide your credentials before accessing "
				#"this resource.")
		#else:
			#msg=_("Please log in.")
			#forward_url= request.headers.get("Referer", "/")
			
		#response.status=403
		#return dict(message=msg, previous_url=previous_url, logging_in=True,
					#original_parameters=request.params,
					#forward_url=forward_url)

	#@expose()
	#def logout(self):
		#identity.current.logout()
		#raise redirect("/")
