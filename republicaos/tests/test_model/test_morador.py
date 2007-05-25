#!/usr/bin/python
# -*- coding: utf-8 -*-

from republicaos.model import *
from elixir import *
from datetime import date, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from base import BaseTest

class TestMorador(BaseTest):
	def test_qts_dias_morados(self):
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 4, 8),
			logradouro = 'R. dos Bobos, nº 0')
		p = Pessoa(nome = 'André')
		m = Morador(pessoa = p, republica = r, data_entrada = date(2007, 5, 8), data_saida = date(2007, 6, 10))
		
		objectstore.flush()
		
		assert m.qtd_dias_morados(date(2007, 4, 8), date(2007, 5, 7)) == 0
		assert m.qtd_dias_morados(date(2007, 5, 8), date(2007, 6, 7)) == 31
		assert m.qtd_dias_morados(date(2007, 6, 8), date(2007, 7, 7)) == 3
		assert m.qtd_dias_morados(date(2007, 7, 8), date(2007, 8, 7)) == 0
	
	
	
	def test_telefonemas(self):
		p1 = Pessoa(nome = 'André')
		
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 3, 6),
			logradouro = 'R. dos Bobos, nº 0')
		
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 3, 6), data_saida = date(2006, 12, 1))
		
		Telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = m1)
		Telefone(numero = 2222, descricao = 'pizzaria', responsavel = m1)
		
		c1 = ContaTelefone(telefone = 2409, companhia = 1, emissao = date(2007, 4, 19), vencimento = date(2007, 5, 2), republica = r)
		c2 = ContaTelefone(telefone = 2409, companhia = 1, emissao = date(2007, 5, 18), vencimento = date(2007, 6, 6), republica = r)
		
		t1 = Telefonema(numero = 1234, conta_telefone = c1, tipo_fone = 1, tipo_distancia = 1, segundos = 150, valor = 1.4)
		t2 = Telefonema(numero = 3333, conta_telefone = c1, tipo_fone = 1, tipo_distancia = 1, segundos = 299, valor = 2.15)
		t3 = Telefonema(numero = 2222, conta_telefone = c1, tipo_fone = 1, tipo_distancia = 1, segundos = 200, valor = 4.0)
		t4 = Telefonema(numero = 2222, conta_telefone = c2, tipo_fone = 1, tipo_distancia = 1, segundos = 300, valor = 2.5)
		t5 = Telefonema(numero = 7777, conta_telefone = c2, tipo_fone = 1, tipo_distancia = 1, segundos = 60,  valor = 0.10)
		
		objectstore.flush()
		
		c1.determinar_responsaveis_telefonemas()
		c2.determinar_responsaveis_telefonemas()
		
		telefonemas_c1 = m1.telefonemas(c1)
		telefonemas_c2 = m1.telefonemas(c2)
		
		assert t1 in telefonemas_c1
		assert t1 not in telefonemas_c2
		assert t2 not in telefonemas_c1
		assert t2 not in telefonemas_c2
		assert t3 in telefonemas_c1
		assert t3 not in telefonemas_c2
		assert t4 in telefonemas_c2
		assert t4 not in telefonemas_c1
		assert t5 not in telefonemas_c1
		assert t5 not in telefonemas_c2
	
	
	
	def test_despesas(self):
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 3, 6),
			logradouro = 'R. dos Bobos, nº 0')
			
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Marcos')
		
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 3, 6), data_saida = date(2006, 12, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 3, 6))
		
		td1 = TipoDespesa(nome = u'Água',    republica = r)
		td2 = TipoDespesa(nome = 'Aluguel',  republica = r)
		td3 = TipoDespesa(nome = 'Internet', republica = r)
		
		d1 = Despesa(data = date(2007, 4, 10), valor = 20, tipo = td1, responsavel = m1)
		d2 = Despesa(data = date(2007, 4, 21), valor = 50, tipo = td2, responsavel = m1)
		d3 = Despesa(data = date(2007, 4, 21), valor = 50, tipo = td2, responsavel = m2)
		
		da1 = DespesaAgendada(dia_vencimento = 19, valor = 50, tipo = td3, responsavel = m1, data_cadastro = date(2006, 12, 1))
		da2 = DespesaAgendada(dia_vencimento = 15, valor = 45, tipo = td1, responsavel = m1, data_cadastro = date(2007, 6, 1))
		
		objectstore.flush()
		
		despesas = m1.despesas(date(2007, 4, 10), date(2007, 5, 10))
		
		assert m1._found(date(2007, 4, 19), da1, despesas)
		assert not m1._found(date(2007, 4, 15), da2, despesas)
		assert d1 in despesas
		assert d2 in despesas
		assert d3 not in despesas
