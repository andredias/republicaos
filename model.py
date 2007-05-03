# -*- coding: utf-8 -*-

from elixir      import Unicode, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, has_field, using_options, using_table_options, using_mapper_options
from elixir      import has_many as one_to_many
from elixir      import belongs_to as many_to_one
from elixir      import has_and_belongs_to_many as many_to_many
from elixir      import metadata, objectstore
from sqlalchemy  import *
from datetime    import date, datetime, time
import csv
from decimal     import Decimal
from dateutil.relativedelta import relativedelta

class Pessoa(Entity):
	has_field('nome', Unicode(80), nullable = False, unique = True)
	using_options(tablename = 'pessoa')
	one_to_many('contatos', of_kind = 'Contato', inverse = 'pessoa', order_by = ['tipo', 'contato'])
	
	def get_telefones():
		return Telefone.select(Telefone.c.id_pessoa_resp == self.id)
	
	def get_emails():
		pass
	
	def get_telefones_contato():
		pass









class Contato(Entity):
	has_field('contato', Unicode(100), nullable = False),
	has_field('tipo', Integer, nullable = False),
	many_to_one('pessoa', of_kind = 'Pessoa', inverse = 'contatos', colname = 'id_pessoa',
		column_kwargs = dict(nullable = False))
	using_options(tablename = 'contato')










class Telefone(Entity):
	'''
	Telefone com alguém responsável.
	
	Relacionado a pessoa e república, independente de ser morador ou não, pois se associado com morador, a data de entrada
	na república também faria parte da chave primária.
	Além disso, economiza nas buscas, já que não é necessário pesquisar na tabela morador pra achar a república.
	'''
	has_field('numero', Numeric(12, 0), primary_key = True)
	has_field('descricao', Unicode)
	using_options(tablename = 'telefone')
	many_to_one('responsavel', of_kind = 'Pessoa', colname = 'id_pessoa_resp', column_kwargs = dict(primary_key = True))
	many_to_one('republica', of_kind = 'Republica', colname = 'id_republica', column_kwargs = dict(primary_key = True))








class Republica(Entity):
	has_field('nome', Unicode(80), nullable = False)
	has_field('data_criacao', Date, default = date.today, nullable = False)
	has_field('proximo_rateio', Date)
	has_field('logradouro', Unicode(150))
	has_field('complemento', Unicode(100))
	has_field('bairro', Unicode(100))
	has_field('cidade', Unicode(80))
	has_field('uf', String(2))
	has_field('cep', String(8))
	using_options(tablename = 'republica')
	one_to_many('fechamentos', of_kind = 'Fechamento', inverse = 'republica', order_by = '-data')
	one_to_many('contas_telefone', of_kind = 'ContaTelefone', inverse = 'republica')
	one_to_many('tipos_despesa', of_kind = 'TipoDespesa', inverse = 'republica')
	
	
	def _proximo_rateio(self):
		if len(self.fechamentos) and ((self.proximo_rateio is None) or (self.proximo_rateio <= self.fechamentos[0].data)):
			self.proximo_rateio = self.fechamentos[0].data + relativedelta(months = 1)
		elif (self.proximo_rateio is None) or (self.proximo_rateio <= self.data_criacao):
			self.proximo_rateio = self.data_criacao + relativedelta(months = 1)
		return self.proximo_rateio
	
	
	def _datas_fechamentos(self):
		'''
		Todas as datas de fechamento em ordem decrescente
		'''
		result = [self._proximo_rateio()]
		result.extend([fechamento.data for fechamento in self.fechamentos])
		result.append(self.data_criacao)
		return result
	
	
	def get_periodo_da_data(self, data_ref):
		'''
		Obtém o período em que a data_ref se encontra
		'''
		data_inicial = None
		data_final   = None
		
		proximo_rateio = self._proximo_rateio()
		if proximo_rateio < data_ref:
			data_inicial = proximo_rateio
			data_final   = data_ref + relativedelta(days = 1)
		elif data_ref < self.data_criacao:
			data_inicial = data_ref
			data_final   = self.data_criacao - relativedelta(days = 1)
		else:
			datas = self._datas_fechamentos()
			for i in range(len(datas) - 1):
				if datas[i] > data_ref >= datas[i + 1]:
					data_final   = datas[i] - relativedelta(days = 1)
					data_inicial = datas[i + 1]
					break
		
		return (data_inicial, data_final)
	
	
	def ultimo_periodo_fechamento(self):
		'''
		Último período de fechamento da república. Caso não haja nenhum, retorna a data em que a república foi criada
		'''
		datas = self._datas_fechamentos()
		if len(datas) > 2:
			return (datas[2], datas[1] - relativedelta(days = 1))
		else:
			return self.proximo_periodo_fechamento()
	
	
	def proximo_periodo_fechamento(self):
		'''
		Último de fechamento até o dia_fechamento do próximo mês
		'''
		datas = self._datas_fechamentos()
		return (datas[1], datas[0] - relativedelta(days = 1))
	
	
	def retifica_periodo(data_inicial, data_final):
		'''
		Se a data inicial é fornecida, determina o período em que ela se encontra, senão, retorna o próximo período de fechamento
		'''
		if data_inicial and not data_final:
			# uma data fornecida. Então deseja o período em que essa data se encontra
			di, df = self.get_periodo_da_data(data_inicial)
			data_inicial = None
		elif not data_inicial:
			# nenhuma data fornecida, obtém o próximo fechamento
			di, df = self.proximo_periodo_fechamento()
		
		if not data_inicial:
			data_inicial = di
		if not data_final:
			data_final = df
		
		# garante que as datas estão em ordem crescente
		if data_inicial > data_final:
			data_inicial, data_final = data_final, data_inicial
		return (data_inicial, data_final)
	
	
	def moradores(self, data_inicial = None, data_final = None):
		'''
		Retorna os moradores da república no período de tempo
		'''
		data_inicial, data_final = self.retifica_periodo(data_inicial, data_final)
		return Pessoa.select(
					and_(
						Morador.c.id_republica == self.id,
						Pessoa.c.id == Morador.c.id_pessoa,
						Morador.c.data_entrada < data_final,
						or_(Morador.c.data_saida >= data_inicial, Morador.c.data_saida == None)
					)
				)
	









class Fechamento(Entity):
	has_field('data', Date, primary_key = True)
	using_options(tablename = 'fechamento')
	many_to_one('republica', of_kind = 'Republica', inverse = 'fechamentos', colname = 'id_republica',
		column_kwargs = dict(primary_key = True))
	
	
	def ratear_despesas(self, data_inicial = None, data_final = None):
		'''
		Calcula a divisão das despesas em determinado período
		'''
		data_inicial, data_final = self.retifica_periodo(data_inicial, data_final)






class ContaTelefone(Entity):
	'''
	Representa cada conta de telefone que chega por mês para a república.
	'''
	# campo id implícito
	has_field('vencimento', Date, nullable = False)
	has_field('emissao', Date, nullable = False)
	has_field('telefone', Numeric(12, 0))
	has_field('companhia', Integer, nullable = False)
	has_field('franquia', Numeric(10,2), default = 0)
	using_options(tablename = 'conta_telefone')
	using_table_options(UniqueConstraint('telefone', 'emissao'))
	many_to_one('republica', of_kind = 'Republica', inverse = 'contas_telefone', colname = 'id_republica',
		column_kwargs = dict(nullable = False))
	one_to_many('telefonemas', of_kind = 'Telefonema', inverse = 'conta_telefone')
	
	def determinar_responsaveis_telefonemas(self):
		'''
		Determina os responsáveis pelos telefonemas da conta
		'''
		responsaveis_telefones = dict(
						select(
								[Telefone.c.numero, Telefone.c.id_pessoa_resp],
								Telefone.c.id_republica == self.id_republica
							).execute().fetchall()
						)
		for telefonema in self.telefonemas:
			if telefonema.responsavel is None and responsaveis_telefones.has_key(telefonema.numero):
				telefonema.responsavel = Pessoa.get_by(id = responsaveis_telefones[telefonema.numero])
		
		objectstore.flush()
	
	
	def interpreta_csv_net_fone(self, linhas):
		# ignora as 3 primeiras linhas de cabeçalho
		linhas = linhas[3:]
		col_numero  = 4
		col_tipo    = 2
		col_duracao = 11
		col_valor   = 13
		telefonemas = dict()
		
		# palavras usadas na descrição que ajudam a classificar o telefonema
		tipos_fone      = ['FIXOS', 'CELULARES', 'NETFONE']
		tipos_distancia = ['LOCAIS', 'DDD', 'DDI'] # confirmar se aparece DDI
		
		# posição das palavras que determinam os tipos dentro da descrição
		col_tipo_fone      = -1
		col_tipo_distancia = 3
		
		for linha in linhas:
			numero  = int(linha[col_numero].strip())
			descr   = linha[col_tipo].split()
			valor   = Decimal(linha[col_valor].strip())
			
			milesimos_minutos = int(linha[col_duracao].strip())
			segundos          = milesimos_minutos * 60 / 1000
			
			tipo_fone      = tipos_fone.index(descr[col_tipo_fone])
			tipo_distancia = tipos_distancia.index(descr[col_tipo_distancia])
			
			if not telefonemas.has_key(numero):
				# não consegui fazer contas apenas com time. Foi necessário usar relativedelta
				telefonemas[numero] = [segundos, valor, tipo_fone, tipo_distancia]
			else:
				telefonemas[numero][0] += segundos
				telefonemas[numero][1] += valor
		
		return telefonemas
	
	
	def importar_csv(self, arquivo, tipo):
		'''
		Importa um arquivo .csv referente a uma conta telefônica de uma operadora.
		
		Qualquer telefonema pré-existente no período de referência fornecido é apagado, e o resultado final fica sendo apenas
		o do arquivo importado
		'''
		
		if tipo == 1:
			func_interpreta_csv = self.interpreta_csv_net_fone
		else:
			func_interpreta_csv = None
		
		linhas      = [linha for linha in csv.reader(arquivo)]
		telefonemas = func_interpreta_csv(linhas)
		
		# antes de registrar os novos telefonemas, é necessário apagar os anteriores do mesmo mês
		Telefonema.table.delete(Telefonema.c.id_conta_telefone == self.id).execute()
		
		# registra os novos telefonemas
		for numero, atributos in telefonemas.iteritems():
			Telefonema(
				numero         = numero,
				conta_telefone = self,
				segundos       = atributos[0],
				valor          = atributos[1],
				tipo_fone      = atributos[2],
				tipo_distancia = atributos[3]
			)
		objectstore.flush()
		self.determinar_responsaveis_telefonemas()
	
	def dividir_conta(self):
		pass



class Telefonema(Entity):
	has_field('numero',         Numeric(12, 0), primary_key = True)
	has_field('tipo_fone',      Integer,        nullable = False)	# fixo, celular, net fone
	has_field('tipo_distancia', Integer,        nullable = False)	# Local, DDD, DDI
	has_field('segundos',       Integer,        nullable = False)
	has_field('valor',          Numeric(10, 2), nullable = False)
	using_options(tablename = 'telefonema')
	many_to_one('responsavel',    of_kind = 'Pessoa',        colname = 'id_pessoa')
	many_to_one('conta_telefone', of_kind = 'ContaTelefone', colname = 'id_conta_telefone', inverse = 'telefonemas', column_kwargs = dict(primary_key = True))


class Morador(Entity):
	has_field('data_entrada', Date, default = date.today, primary_key = True)
	has_field('data_saida', Date)
	using_options(tablename = 'morador')
	many_to_one('republica', of_kind = 'Republica', inverse = 'moradores', colname = 'id_republica',
		column_kwargs = dict(primary_key = True))
	many_to_one('pessoa', of_kind = 'Pessoa', colname = 'id_pessoa',
		column_kwargs = dict(primary_key = True))
	
	
	def despesas(self, data_inicial = None, data_final = None):
		data_inicial, data_final = self.republica.retifica_periodo(data_inicial, data_final)
		return Despesa.select(
					and_(
						Despesa.c.id_pessoa    == self.id_pessoa,
						Despesa.c.id_republica == self.id_republica,
						data_inicial           <= Despesa.c.data,
						Despesa.c.data         <= data_final
						),
					order_by = Despesa.c.data
					)
	
	def telefonemas(self, data_inicial = None, data_final = None):
		data_inicial, data_final = self.republica.retifica_periodo(data_inicial, data_final)
		return Telefonema.select(
					and_(
						Telefonema.c.id_pessoa   == self.id_pessoa,
						Telefonema.c.id_conta_telefone == ContaTelefone.c.id,
						ContaTelefone.c.id_republica == self.id_republica,
						data_inicial <= ContaTelefone.c.vencimento,
						ContaTelefone.c.vencimento <= data_final
						),
					order_by = Telefonema.c.telefone
					)
	
	def qtd_dias_morados(self, data_inicial, data_final):
		data_inicial, data_final = self.republica.retifica_periodo(data_inicial, data_final)
		entrada = max(self.data_entrada, data_inicial)
		if not self.data_saida:
			saida = data_final
		else:
			saida = min(self.data_saida, data_final)
		
		return (entrada - saida).days


class TipoDespesa(Entity):
	has_field('tipo', Unicode(40), nullable = False)
	has_field('descricao', String)
	using_options(tablename = 'tipo_despesa')
	many_to_one('republica', of_kind = 'Republica', inverse = 'tipo_despesas', column_kwargs = dict(nullable = False))


class Despesa(Entity):
	has_field('data', Date, default = date.today, nullable = False)
	has_field('valor', Numeric(10, 2), nullable = False)
	using_options(tablename = 'despesa')
	many_to_one('pessoa',       of_kind = 'Pessoa',      colname = 'id_pessoa',       column_kwargs = dict(nullable = False))
	many_to_one('republica',    of_kind = 'Republica',   colname = 'id_republica',    column_kwargs = dict(nullable = False))
	many_to_one('tipo_despesa', of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))
