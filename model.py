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
	one_to_many('contatos', of_kind = 'Contato', inverse = 'pessoa')
	one_to_many('telefones', of_kind = 'Telefone', inverse = 'responsavel')









class Contato(Entity):
	has_field('contato', Unicode(100), nullable = False),
	has_field('tipo', Integer, nullable = False),
	many_to_one('pessoa', of_kind = 'Pessoa', inverse = 'contatos', colname = 'id_pessoa',
		column_kwargs = dict(nullable = False))
	using_options(tablename = 'contato')









class Telefone(Entity):
	has_field('numero', Numeric(12, 0), primary_key = True)
	has_field('descricao', Unicode)
	using_options(tablename = 'telefone')
	many_to_one('responsavel', of_kind = 'Pessoa',
		inverse = 'telefones', colname = 'id_pessoa_resp',
		column_kwargs = dict(primary_key = True))








class Republica(Entity):
	has_field('nome', Unicode(80), nullable = False)
	has_field('data_criacao', Date, default = date.today, nullable = False)
	has_field('logradouro', Unicode(150))
	has_field('complemento', Unicode(100))
	has_field('bairro', Unicode(100))
	has_field('cidade', Unicode(80))
	has_field('uf', String(2))
	has_field('cep', String(8))
	using_options(tablename = 'republica')
	one_to_many('fechamentos', of_kind = 'Fechamento', inverse = 'republica', order_by = 'data')
	one_to_many('contas_telefone', of_kind = 'ContaTelefone', inverse = 'republica')
	one_to_many('tipos_despesa', of_kind = 'TipoDespesa', inverse = 'republica')
	
	
	def ultimo_fechamento(self):
		'''
		Último período de fechamento da república. Caso não haja nenhum, retorna a data em que a república foi criada
		'''
		tamanho = len(self.fechamentos)
		if tamanho > 0:
			data_final = self.fechamentos[-1].data
		else:
			data_final = date.today()
		
		if tamanho > 1:
			data_inicial = self.fechamentos[-2].data
		else:
			data_inicial = self.data_criacao
			
		return (data_inicial, data_final)
	
	
	def proximo_fechamento(self):
		'''
		Último de fechamento até o data atual
		'''
		if len(self.fechamentos) > 0:
			data_inicial = self.fechamentos[-1].data
		else:
			data_inicial = self.data_criacao
		
		return (data_inicial, date.today())
	
	
	def moradores(self, data_inicial = None, data_final = None):
		'''
		Retorna os moradores da república no período de tempo
		'''
		di, df = self.proximo_fechamento()
		if not data_inicial:
			data_inicial = di
		if not data_final:
			data_final = df
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






class ContaTelefone(Entity):
	has_field('telefone', Numeric(12, 0), primary_key = True)
	has_field('companhia', Integer, nullable = False)
	using_options(tablename = 'conta_telefone')
	many_to_one('republica', of_kind = 'Republica', inverse = 'contas_telefone', colname = 'id_republica',
		column_kwargs = dict(nullable = False))
	
	
	def telefonemas(self, ano, mes):
		periodo_ref = ano * 100 + mes
		return Telefonema.select(
				and_(
					Telefonema.c.periodo_ref == periodo_ref,
					Telefonema.c.id_conta_telefone == self.telefone
					)
				)
	
	
	def determinar_responsaveis_telefonemas(self, ano, mes):
		telefonemas = self.telefonemas(ano, mes)
		responsavel_telefone = dict( 
						select([Telefone.c.numero, Telefone.c.id_pessoa_resp],
								and_(
									Telefone.c.id_pessoa_resp == Morador.c.id_pessoa,
									Morador.c.id_republica == self.id_republica
									)
							).execute().fetchall()
						)
		for telefonema in telefonemas:
			if telefonema.responsavel == None and responsavel_telefone.has_key(telefonema.numero):
				telefonema.responsavel = Pessoa.get_by(id = responsavel_telefone[telefonema.numero])
		
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
	
	
	def importar_csv(self, arquivo, tipo, ano, mes):
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
		periodo_ref = ano * 100 + mes
		Telefonema.table.delete(and_(Telefonema.c.periodo_ref == periodo_ref, Telefonema.c.id_conta_telefone == self.telefone)).execute()
		
		# registra os novos telefonemas
		for numero, atributos in telefonemas.iteritems():
			Telefonema(
				periodo_ref    = periodo_ref,
				numero         = numero,
				conta_telefone = self,
				segundos       = atributos[0],
				valor          = atributos[1],
				tipo_fone      = atributos[2],
				tipo_distancia = atributos[3]
			)
		objectstore.flush()
		self.determinar_responsaveis_telefonemas(ano = ano, mes = mes)



class Telefonema(Entity):
	has_field('periodo_ref', Integer, primary_key = True)
	has_field('numero', Numeric(12, 0), primary_key = True)
	has_field('tipo_fone', Integer, nullable = False)			# fixo, celular, net fone
	has_field('tipo_distancia', Integer, nullable = False)	# Local, DDD, DDI
	has_field('segundos', Integer, nullable = False)
	has_field('valor', Numeric(8, 2), nullable = False)
	using_options(tablename = 'telefonema')
	many_to_one('responsavel', of_kind = 'Pessoa', colname = 'id_pessoa_resp')
	many_to_one('conta_telefone', of_kind = 'ContaTelefone',
		colname = 'id_conta_telefone', column_kwargs = dict(primary_key = True))




class Morador(Entity):
	has_field('data_entrada', Date, default = date.today, primary_key = True)
	has_field('data_saida', Date)
	using_options(tablename = 'morador')
	many_to_one('republica', of_kind = 'Republica', inverse = 'moradores', colname = 'id_republica',
		column_kwargs = dict(primary_key = True))
	many_to_one('pessoa', of_kind = 'Pessoa', colname = 'id_pessoa',
		column_kwargs = dict(primary_key = True))




class TipoDespesa(Entity):
	has_field('tipo', Unicode(40), nullable = False)
	has_field('descricao', String)
	using_options(tablename = 'tipo_despesa')
	many_to_one('republica', of_kind = 'Republica', inverse = 'tipo_despesas',
		column_kwargs = dict(nullable = False))


class Despesa(Entity):
	has_field('data', Date, default = date.today, nullable = False)
	has_field('valor', Numeric(8, 2), nullable = False)
	using_options(tablename = 'despesa')
	many_to_one('pessoa', of_kind = 'Pessoa', column_kwargs = dict(nullable = False))
	many_to_one('republica', of_kind = 'Republica', column_kwargs = dict(nullable = False))
	many_to_one('tipo_despesa', of_kind = 'TipoDespesa', column_kwargs = dict(nullable = False))
