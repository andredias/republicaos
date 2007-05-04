#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from datetime import date, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from tests.base import BaseTest



class TestRepublica(BaseTest):
	def test_retifica_periodo(self):
		'''
		Testa a retificação do período
		'''
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 4, 8),
			logradouro = 'R. dos Bobos, nº 0')
		
		Fechamento(republica = r, data = date(2007, 5, 8))
		Fechamento(republica = r, data = date(2007, 6, 10))
		
		objectstore.flush()
		
		assert (date(2007, 5, 8), date(2007, 6, 9)) == r.retifica_periodo(date(2007, 5, 20))
		assert (date(2007, 5, 8), date(2007, 6, 9)) == r.retifica_periodo(date(2007, 6, 9), date(2007, 5, 8))
		assert (date(2007, 6, 10), date(2007, 7, 9)) == r.retifica_periodo()
	
	def test_proximo_periodo_fechamento_contas_republica(self):
		'''
		Testa se o próximo fechamento está no intervalo correto.
		
		O intervalo esperado é [data_ultimo_periodo_fechamento, data_ultimo_periodo_fechamento + 1 mês - 1 dia] ou escrito de outra forma
		[data_ultimo_periodo_fechamento, data_ultimo_periodo_fechamento + 1 mês[
		'''
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 4, 8),
			logradouro = 'R. dos Bobos, nº 0')
		
		objectstore.flush()
		assert (date(2007, 4, 8), date(2007, 5, 7)) == r.proximo_periodo_fechamento()
		
		Fechamento(data = date(2007, 5, 10), republica = r)
		r.proximo_rateio = None
		objectstore.flush()
		
		# devido a um defeito no sqlalchemy/elixir, o backref não está sendo atualizado automaticamente
		# vai ser necessário obter o objeto de novo
		objectstore.clear()
		r = Republica.get_by(id = 1)
		
		assert (date(2007, 5, 10), date(2007, 6, 9)) == r.proximo_periodo_fechamento()
		
		r.proximo_rateio = date(2007, 6, 1)
		assert (date(2007, 5, 10), date(2007, 5, 31)) == r.proximo_periodo_fechamento()
	
	
	def test_fechamento_contas(self):
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 4, 8),
			logradouro = 'R. dos Bobos, nº 0')
		
		Fechamento(data = date(2007, 5, 10), republica = r)
		objectstore.flush()
		
		# devido a um defeito no sqlalchemy/elixir, o backref não está sendo atualizado automaticamente
		# vai ser necessário obter o objeto de novo
		objectstore.clear()
		r = Republica.get_by(id = 1)
		
		assert (date(2007, 4, 8), date(2007, 5, 9)) == r.ultimo_periodo_fechamento()
		
		Fechamento(data = date(2007, 6, 7), republica = r)
		objectstore.flush()
		
		# devido a um defeito no sqlalchemy/elixir, o backref não está sendo atualizado automaticamente
		# vai ser necessário obter o objeto de novo
		objectstore.clear()
		r = Republica.get_by(id = 1)
		
		assert (date(2007, 5, 10), date(2007, 6, 6)) == r.ultimo_periodo_fechamento()