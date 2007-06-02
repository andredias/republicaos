#!/usr/bin/python
# -*- coding: utf-8 -*-

import decimal

from republicaos.model.business import *
from elixir import *
from datetime import date
from decimal import Decimal
from base import BaseTest
from exibicao_resultados import print_acerto_final

class TestFechamentoContas(BaseTest):
	'''
	Testa o fechamento das contas do mês
	'''
	#url = 'postgres://turbo_gears:tgears@localhost/tg_teste'
		
	def setup(self):
		BaseTest.setup(self)
		
		self.r = Republica(nome = 'Teste', data_criacao = date(2007, 3, 6), logradouro = 'R. dos Bobos, nº 0')
		
		self.p1 = Pessoa(nome = u'André')
		self.p2 = Pessoa(nome = 'Marcos')
		self.p3 = Pessoa(nome = 'Roger')
		self.p4 = Pessoa(nome = 'Leonardo')
		
		self.c = ContaTelefone(
				telefone = 2409,
				id_operadora = 1,
				emissao = date(2007, 4, 29),
				vencimento = date(2007, 5, 2),
				franquia = Decimal(30),
				servicos = Decimal(0),
				republica = self.r
			)
		
		Fechamento(republica = self.r, data = date(2007, 4, 6))
		
		self.td1 = TipoDespesa(nome = u'Água',    republica = self.r)
		self.td2 = TipoDespesa(nome = 'Aluguel',  republica = self.r)
		self.td3 = TipoDespesa(nome = 'Luz',      republica = self.r)
		self.td4 = TipoDespesa(nome = 'Internet', republica = self.r)
		self.td5 = TipoDespesa(nome = 'Telefone', republica = self.r, especifica = True)
		
		objectstore.flush()
	
	
	def ajustar_fechamento_para_acerto_final(self, f):
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		objectstore.flush()
		
		f.rateio = dict()
		f.rateio[self.m1] = MoradorRateio()
		f.rateio[self.m2] = MoradorRateio()
		f.rateio[self.m3] = MoradorRateio()
		f.rateio[self.m4] = MoradorRateio()
		f.moradores    = f.rateio.keys()
		f.ex_moradores = []
		f.participantes = f.moradores + f.ex_moradores
	
	
	
	def test_acerto_final_1(self):
		'''
		Acerto Final - Caso 1: 2 credores e 2 devedores
		'''
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		self.ajustar_fechamento_para_acerto_final(f)
		
		f.rateio[self.m1].saldo_final = Decimal(-84)
		f.rateio[self.m2].saldo_final = Decimal(166)
		f.rateio[self.m3].saldo_final = Decimal('-154.50')
		f.rateio[self.m4].saldo_final = Decimal('72.50')
		
		f._executar_acerto_final()
		print_acerto_final(f)
		
		assert self.m1 not in f.acerto_a_pagar.keys()
		assert self.m3 not in f.acerto_a_pagar.keys()
		assert self.m2 in f.acerto_a_pagar.keys()
		assert self.m4 in f.acerto_a_pagar.keys()
		assert (self.m1 in f.acerto_a_pagar[self.m2]) and f.acerto_a_pagar[self.m2][self.m1] == Decimal('84.00')
		assert (self.m3 in f.acerto_a_pagar[self.m2]) and f.acerto_a_pagar[self.m2][self.m3] == Decimal('82.00')
		assert (self.m3 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m3] == Decimal('72.50')
	
	
	
	def test_acerto_final_2(self):
		'''
		Acerto Final - Caso 2: 1 credor e 3 devedores
		'''
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		self.ajustar_fechamento_para_acerto_final(f)
		
		f.rateio[self.m1].saldo_final = Decimal(30)
		f.rateio[self.m2].saldo_final = Decimal(15)
		f.rateio[self.m3].saldo_final = Decimal(35)
		f.rateio[self.m4].saldo_final = Decimal(-80)
		
		f._executar_acerto_final()
		print_acerto_final(f)
		
		assert self.m1 in f.acerto_a_pagar.keys()
		assert self.m2 in f.acerto_a_pagar.keys()
		assert self.m3 in f.acerto_a_pagar.keys()
		assert self.m4 not in f.acerto_a_pagar.keys()
		assert (self.m4 in f.acerto_a_pagar[self.m1]) and f.acerto_a_pagar[self.m1][self.m4] == Decimal(30)
		assert (self.m4 in f.acerto_a_pagar[self.m2]) and f.acerto_a_pagar[self.m2][self.m4] == Decimal(15)
		assert (self.m4 in f.acerto_a_pagar[self.m3]) and f.acerto_a_pagar[self.m3][self.m4] == Decimal(35)
		assert len(f.acerto_a_pagar[self.m1]) == len(f.acerto_a_pagar[self.m2]) == len(f.acerto_a_pagar[self.m3]) == 1
	
	
	
	def test_acerto_final_3(self):
		'''
		Acerto Final - Caso 3: 3 credores e 1 devedor
		'''
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		self.ajustar_fechamento_para_acerto_final(f)
		
		f.rateio[self.m1].saldo_final = Decimal(-30)
		f.rateio[self.m2].saldo_final = Decimal(-15)
		f.rateio[self.m3].saldo_final = Decimal(-35)
		f.rateio[self.m4].saldo_final = Decimal(80)
		
		f._executar_acerto_final()
		print_acerto_final(f)
		
		assert self.m1 not in f.acerto_a_pagar.keys()
		assert self.m2 not in f.acerto_a_pagar.keys()
		assert self.m3 not in f.acerto_a_pagar.keys()
		assert self.m4 in f.acerto_a_pagar.keys() and len(f.acerto_a_pagar) == 1
		assert (self.m1 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m1] == Decimal(30)
		assert (self.m2 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m2] == Decimal(15)
		assert (self.m3 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m3] == Decimal(35)
	
	
	def test_acerto_final_4(self):
		'''
		Acerto Final - Caso 4: 0 credores e 0 devedores
		'''
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		self.ajustar_fechamento_para_acerto_final(f)
		
		f.rateio[self.m1].saldo_final = Decimal(0)
		f.rateio[self.m2].saldo_final = Decimal(0)
		f.rateio[self.m3].saldo_final = Decimal(0)
		f.rateio[self.m4].saldo_final = Decimal(0)
		
		f._executar_acerto_final()
		print_acerto_final(f)
		
		assert len(f.acerto_a_pagar) == 0
	
	
	def test_fechamento_1(self):
		from test_dividir_conta_telefone import TestDividirContaTelefone
		from exibicao_resultados         import print_rateio_conta_telefone, print_fechamento
		# utiliza o test_dividir_conta_telefone
		testa_conta = TestDividirContaTelefone()
		testa_conta.r = self.r
		testa_conta.c = self.c
		testa_conta.p1 = self.p1
		testa_conta.p2 = self.p2
		testa_conta.p3 = self.p3
		testa_conta.p4 = self.p4
		
		testa_conta.test_dividir_conta_caso_15()
		
		self.m1 = testa_conta.m1
		self.m2 = testa_conta.m2
		self.m3 = testa_conta.m3
		self.m4 = testa_conta.m4
		
		Despesa(data = date(2007, 4, 21), quantia = 20, tipo = self.td1, responsavel = self.m1)
		Despesa(data = date(2007, 4, 12), quantia = 50, tipo = self.td3, responsavel = self.m2)
		Despesa(data = date(2007, 4, 21), quantia = 150, tipo = self.td2, responsavel = self.m2)
		Despesa(data = date(2007, 5, 1), quantia = 150, tipo = self.td2, responsavel = self.m3)
		Despesa(data = date(2007, 5, 5), quantia = self.c.resumo['total_conta'], tipo = self.td5, responsavel = self.m1)
		
		DespesaPeriodica(quantia = 50, tipo = self.td4, responsavel = self.m1, proximo_vencimento = date(2007, 4, 19))
		DespesaPeriodica(quantia = 45, tipo = self.td1, responsavel = self.m1, proximo_vencimento = date(2007, 6, 1))
		
		objectstore.flush()
		
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		f.executar_rateio()
		print_fechamento(f)
		
		assert f.total_despesas_gerais > 0 and f.total_despesas_especificas > 0
		assert f.total_despesas_gerais == sum(morador.quota_geral for morador in f.rateio.values())
		assert f.total_despesas_especificas == self.c.resumo['total_conta'] == sum(morador.quota_especifica for morador in f.rateio.values())
		assert len(f.moradores) == 3 and len(f.ex_moradores) == 1
		assert any(morador.saldo_final for morador in f.rateio.values())
		assert sum(morador.saldo_final for morador in f.rateio.values()) == 0
	
	
	def test_fechamento_2(self):
		'''
		Fechamento sem nenhum ex-morador
		'''
		from test_dividir_conta_telefone import TestDividirContaTelefone
		from exibicao_resultados         import print_rateio_conta_telefone, print_fechamento
		# utiliza o test_dividir_conta_telefone
		testa_conta = TestDividirContaTelefone()
		testa_conta.r = self.r
		testa_conta.c = self.c
		testa_conta.p1 = self.p1
		testa_conta.p2 = self.p2
		testa_conta.p3 = self.p3
		
		testa_conta.test_dividir_conta_caso_07()
		
		self.m1 = testa_conta.m1
		self.m2 = testa_conta.m2
		self.m3 = testa_conta.m3
		
		Despesa(data = date(2007, 4, 21), quantia = 20, tipo = self.td1, responsavel = self.m1)
		Despesa(data = date(2007, 4, 12), quantia = 50, tipo = self.td3, responsavel = self.m2)
		Despesa(data = date(2007, 4, 21), quantia = 150, tipo = self.td2, responsavel = self.m2)
		Despesa(data = date(2007, 5, 1), quantia = 150, tipo = self.td2, responsavel = self.m3)
		Despesa(data = date(2007, 5, 5), quantia = (self.c.resumo['total_conta'] / 2), tipo = self.td5, responsavel = self.m1)
		Despesa(data = date(2007, 5, 5), quantia = (self.c.resumo['total_conta'] / 2), tipo = self.td5, responsavel = self.m2)
		
		DespesaPeriodica(quantia = 150, tipo = self.td4, responsavel = self.m1, proximo_vencimento = date(2007, 4, 19))
		DespesaPeriodica(quantia = 45, tipo = self.td1, responsavel = self.m1, proximo_vencimento = date(2007, 6, 1))
		
		objectstore.flush()
		
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		f.executar_rateio()
		print_fechamento(f)
		
		assert f.total_despesas_gerais > 0 and f.total_despesas_especificas > 0
		assert f.total_despesas_gerais == sum(morador.quota_geral for morador in f.rateio.values())
		assert f.total_despesas_especificas == self.c.resumo['total_conta'] == sum(morador.quota_especifica for morador in f.rateio.values())
		assert len(f.moradores) == 3 and len(f.ex_moradores) == 0
		assert any(morador.saldo_final for morador in f.rateio.values())
		assert sum(morador.saldo_final for morador in f.rateio.values()) == 0
	
	
	def test_fechamento_3(self):
		'''
		Fechamento sem nenhum morador
		'''
		from test_dividir_conta_telefone import TestDividirContaTelefone
		from exibicao_resultados         import print_rateio_conta_telefone, print_fechamento
		
		f = Fechamento(republica = self.r, data = date(2007, 5, 6))
		f.executar_rateio()
		print_fechamento(f)
		
		assert f.total_despesas_gerais == 0 and f.total_despesas_especificas == 0
		assert len(f.moradores) == 0 and len(f.ex_moradores) == 0





