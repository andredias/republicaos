# -*- coding: utf-8 -*-

from elixir      import Unicode, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, has_field, using_options, using_table_options, using_mapper_options
from elixir      import has_many as one_to_many
from elixir      import belongs_to as many_to_one
from elixir      import has_and_belongs_to_many as many_to_many
from elixir      import metadata, objectstore
from sqlalchemy  import *
from datetime    import date, datetime
import time

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
	one_to_many('fechamentos', of_kind = 'Fechamento', inverse = 'republica')
	one_to_many('contas_telefone', of_kind = 'ContaTelefone', inverse = 'republica')
	one_to_many('tipos_despesa', of_kind = 'TipoDespesa', inverse = 'republica')
	
	
	def ultimo_fechamento(self):
		'''
		Último fechamento da república. Caso não haja nenhum, retorna a data em que a república foi criada
		'''
		
		# retorna uma string com a data e não um objeto datetime
		# pelo menos no SQLite
		data = select(
				[func.max(Fechamento.c.data)],
				Fechamento.c.id_republica == self.id
			).execute().fetchone()[0]
		
		if data == None:
			data = self.data_criacao
		elif type(data) != type(self.data_criacao):
			# transforma a string em data
			partes = time.strptime(data,'%Y-%m-%d')
			data = date(partes[0], partes[1], partes[2])
		return data
	
	
	def moradores(self, data_inicial = None, data_final = None):
		'''
		Retorna os moradores da república no período de tempo
		'''
		if not data_inicial:
			data_inicial = self.ultimo_fechamento()
		# não sei se por data.today() como valor default garante que vai ser calculado a cada chamada
		if not data_final:
			data_final = date.today()
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
		
	def _determinar_periodo(self, data_inicial, data_final):
		if not data_inicial:
			data_inicial = self.republica.ultimo_fechamento()
		if not data_final:
			data_final = data_inicial
		self._periodo_inicial = data_inicial.year * 100 + data_inicial.month
		self._periodo_final   = data_final.year * 100 + data_final.month
	
	
	def telefonemas(self, data_inicial = None, data_final = None):
		self._determinar_periodo(data_inicial, data_final)
		return Telefonema.select(
				and_(
					Telefonema.c.periodo_ref >= self._periodo_inicial,
					Telefonema.c.periodo_ref <= self._periodo_final,
					Telefonema.c.id_conta_telefone == self.telefone
					)
				)
	
	
	def determinar_responsaveis_telefonemas(self, data_inicial = None, data_final = None):
		telefonemas = self.telefonemas(data_inicial, data_final)
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




class Telefonema(Entity):
	has_field('periodo_ref', Integer, primary_key = True)
	has_field('numero', Numeric(12, 0), primary_key = True)
	has_field('tipo_fone', Integer, nullable = False)			# fixo, celular, net fone
	has_field('tipo_distancia', Integer, nullable = False)	# Local, DDD, DDI
	has_field('duracao', Time, nullable = False)
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
