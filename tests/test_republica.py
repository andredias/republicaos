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
	
	
	def test_contas_telefone(self):
		r1 = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), logradouro = 'R. dos Bobos, nº 0')
		r2 = Republica(nome = 'Teste2', data_criacao = date(2007, 5, 8), logradouro = 'R. dos Bobos, nº 1')
		
		c1 = ContaTelefone(telefone = 11, companhia = 1, emissao = date(2007, 4, 29), vencimento = date(2007, 5, 10), republica = r1)
		c2 = ContaTelefone(telefone = 11, companhia = 2, emissao = date(2007, 5, 29), vencimento = date(2007, 5, 10), republica = r1)
		c3 = ContaTelefone(telefone = 11, companhia = 2, emissao = date(2007, 6, 21), vencimento = date(2007, 5, 10), republica = r1)
		c4 = ContaTelefone(telefone = 22, companhia = 1, emissao = date(2007, 4, 29), vencimento = date(2007, 5, 10), republica = r2)
		c5 = ContaTelefone(telefone = 22, companhia = 1, emissao = date(2007, 5, 10), vencimento = date(2007, 5, 10), republica = r2)
		
		objectstore.flush()
		
		assert len(r1.contas_telefone(date(2007, 1, 8), date(2007, 4, 28))) == 0
		assert len(r1.contas_telefone(date(2007, 4, 29), date(2007, 5, 29))) == 2
		assert len(r1.contas_telefone(date(2007, 4, 29), date(2007, 6, 21))) == 3
		assert c1 in r1.contas_telefone(date(2007, 4, 29), date(2007, 5, 29))
		assert c2 in r1.contas_telefone(date(2007, 4, 29), date(2007, 5, 29))
		assert c3 in r1.contas_telefone(date(2007, 4, 29), date(2007, 6, 21))
		
		assert len(r2.contas_telefone(date(2007, 4, 29), date(2007, 6, 29))) == 2
	
	
	def test_moradores(self):
		'''
		Testa quais moradores entram ou não em um determinado período de fechamento.
		
		Escrito de outras formas, o período de apuração pode ser definido como:
		   * `[dia/mês, dia/(mês+1)[`
		   * `----[xxxxxx[`--->`
		
		Caos de apuração:
		
		                        Período de Apuração
		-------------------[xxxxxxxxxxxxxxxxxxxxxxxxxxxxx[------------------>    Morador     |  Incluído
		                   |                             |
		-------[xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-->    Morador_1   |  X
		                   |                             |
		------------------------[xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-->    Morador_2   |  X
		                   |                             |
		-------[xxxxxxxxxxxxxxxxxxxxxxxxxx]--------------------------------->    Morador_3   |  X
		                   |                             |
		--------------------------[xxxxxxxxx]------------------------------->    Morador_4   |  X
		                   |                             |
		--------------------------------------------------------[xxxxxxxxx-->    Morador_5   |      
		                   |                             |
		-------------------------------------------------[xxxxxxxx]--------->    Morador_6   |      
		                   |                             |
		-------[xxxxxxxx]--------------------------------------------------->    Morador_7   |      
		                   |                             |
		---------[xxxxxxxxx]------------------------------------------------>    Morador_8   |  X
		'''
		r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), logradouro = 'R. dos Bobos, nº 0')
		
		p1 = Pessoa(nome = '1')
		p2 = Pessoa(nome = '2')
		p3 = Pessoa(nome = '3')
		p4 = Pessoa(nome = '4')
		p5 = Pessoa(nome = '5')
		p6 = Pessoa(nome = '6')
		p7 = Pessoa(nome = '7')
		p8 = Pessoa(nome = '8')
		
		# período de apuração = 2007-03-10 até 2007-04-09
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 2, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 3, 20))
		m3 = Morador(pessoa = p3, republica = r, data_entrada = date(2007, 2, 1), data_saida = date(2007, 3, 20))
		m4 = Morador(pessoa = p4, republica = r, data_entrada = date(2007, 3, 20), data_saida = date(2007, 4, 4))
		m5 = Morador(pessoa = p5, republica = r, data_entrada = date(2007, 4, 20))
		m6 = Morador(pessoa = p6, republica = r, data_entrada = date(2007, 4, 10), data_saida = date(2007, 5, 4))
		m7 = Morador(pessoa = p7, republica = r, data_entrada = date(2007, 2, 1), data_saida = date(2007, 3, 1))
		m8 = Morador(pessoa = p8, republica = r, data_entrada = date(2007, 2, 1), data_saida = date(2007, 3, 10))
		
		objectstore.flush()
		
		moradores = r.moradores(date(2007, 3, 10), date(2007, 4, 9))
		
		assert m1 in moradores
		assert m2 in moradores
		assert m3 in moradores
		assert m4 in moradores
		assert m5 not in moradores
		assert m6 not in moradores
		assert m7 not in moradores
		assert m8 in moradores

