#!/usr/bin/python
# -*- coding: utf-8 -*-

import decimal

from republicaos.model.business import *
from elixir import *
from datetime import date
from decimal import Decimal
from base import BaseTest
from exibicao_resultados import print_acerto_final, print_calculo_quotas_participantes
from pronus_utils import float_equal

class TestFechamento(BaseTest):
	'''
	Testa o fechamento das contas do mês
	'''
	#url = 'postgres://turbo_gears:tgears@localhost/tg_teste'
		
	def setup(self):
		BaseTest.setup(self)
		
		self.r = Republica(nome = 'Teste', data_criacao = date(2007, 3, 6), logradouro = 'R. dos Bobos, nº 0')
		self.r.flush()
		
		self.r.criar_fechamento(data = date(2007, 4, 6))
		
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
		
		
		self.td1 = TipoDespesa(nome = u'Água',    republica = self.r)
		self.td2 = TipoDespesa(nome = 'Aluguel',  republica = self.r)
		self.td3 = TipoDespesa(nome = 'Luz',      republica = self.r)
		self.td4 = TipoDespesa(nome = 'Internet', republica = self.r)
		self.td5 = TipoDespesa(nome = 'Telefone', republica = self.r)
		
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
	
	
	def test_periodo_fechamento(self):
		f1 = self.r.fechamentos[0]
		f2 = self.r.criar_fechamento(data = date(2007, 5, 6))
		f3 = self.r.criar_fechamento(data = date(2007, 6, 6))
		
		f1.executar_rateio()
		f2.executar_rateio()
		f3.executar_rateio()
		
		print 'republica: ', self.r
		print 'fechamentos:'
		for f in self.r.fechamentos:
			print f
		
		assert f1.data_inicial == self.r.data_criacao and f1.data_final == (f1.data - relativedelta(days = 1))
		assert f2.data_inicial == f1.data and f2.data_final == (f2.data - relativedelta(days = 1))
		assert f3.data_inicial == f2.data and f3.data_final == (f3.data - relativedelta(days = 1))
	
	
	
	def test_acerto_final_1(self):
		'''
		Acerto Final - Caso 1: 2 credores e 2 devedores
		'''
		f = self.r.criar_fechamento(data = date(2007, 5, 6))
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
		assert sum(quantia for quantia in f.acerto_a_pagar[self.m2].values()) == Decimal(166)
		assert sum(quantia for quantia in f.acerto_a_pagar[self.m4].values()) == Decimal('72.50')
		assert sum(quantia for quantia in f.acerto_a_receber[self.m1].values()) == Decimal(84)
		assert sum(quantia for quantia in f.acerto_a_receber[self.m3].values()) == Decimal('154.50')
	
	
	
	def test_acerto_final_2(self):
		'''
		Acerto Final - Caso 2: 1 credor e 3 devedores
		'''
		f = self.r.criar_fechamento(data = date(2007, 5, 6))
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
		f = self.r.criar_fechamento(data = date(2007, 5, 6))
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
		f = self.r.criar_fechamento(data = date(2007, 5, 6))
		self.ajustar_fechamento_para_acerto_final(f)
		
		f.rateio[self.m1].saldo_final = Decimal(0)
		f.rateio[self.m2].saldo_final = Decimal(0)
		f.rateio[self.m3].saldo_final = Decimal(0)
		f.rateio[self.m4].saldo_final = Decimal(0)
		
		f._executar_acerto_final()
		print_acerto_final(f)
		
		assert len(f.acerto_a_pagar) == 0
	
	
	def assert_geral_fechamento(self, fechamento):
		assert fechamento.total_despesas > 0
		assert any(morador.saldo_final for morador in fechamento.rateio.values())
		assert float_equal(fechamento.total_despesas, sum(fechamento.rateio[morador].quota for morador in fechamento.participantes) + fechamento.total_telefone)
		assert float_equal(sum(morador.saldo_final for morador in fechamento.rateio.values()), 0.0)
		for credor, creditos in fechamento.acerto_a_receber.items():
			assert sum(creditos.values()) == abs(fechamento.rateio[credor].saldo_final)
		for devedor, dividas in fechamento.acerto_a_pagar.items():
			assert sum(dividas.values()) == fechamento.rateio[devedor].saldo_final
		
	
	
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
		testa_conta.p5 = self.p5 = Pessoa(nome = 'Alexandre')
		self.p5.flush()
		
		f = self.r.criar_fechamento(data = date(2007, 5, 6))
		
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
		
		f.executar_rateio()
		print_fechamento(f)
		
		assert len(f.participantes) == 5
		self.assert_geral_fechamento(f)
	
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
		
		f = self.r.criar_fechamento()
		
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
		
		f.executar_rateio()
		print_fechamento(f)
		
		assert f.total_telefone == self.c.resumo['total_conta']
		assert len(f.participantes) == 3
		self.assert_geral_fechamento(f)
	
	
	def test_fechamento_3(self):
		'''
		Fechamento sem nenhum morador
		'''
		from test_dividir_conta_telefone import TestDividirContaTelefone
		from exibicao_resultados         import print_rateio_conta_telefone, print_fechamento
		
		f = self.r.criar_fechamento(data = date(2007, 5, 6))
		f.executar_rateio()
		print_fechamento(f)
		
		assert f.total_despesas == 0
		assert len(f.participantes) == 0
		assert sum(morador.saldo_final for morador in f.rateio.values()) == 0
	
	
	def test_calculo_quotas_participantes_1(self):
		'''
		Teste do cálculo da proporção de cada morador. Único intervalo e sem porcentagem cadastrada
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 5, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 5, 6))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 5, 6))
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 1
		assert f.intervalos[0].data_inicial == date(2007, 4, 6)
		assert f.intervalos[0].data_final   == date(2007, 5, 6)
		assert len(f.participantes) == 4
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		
		for morador in f.participantes:
			assert f.quota(morador) == f.quota_peso(morador) == 25
		
		
	def test_calculo_quotas_participantes_2(self):
		'''
		Teste do cálculo da proporção de cada morador. Sem porcentagem cadastrada. Um morador sai em um dia e outro entra no dia seguinte
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 20))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 5, 6))
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 2
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 21)
		assert f.intervalos[1].data_inicial == date(2007, 4, 21) and f.intervalos[1].data_final == date(2007, 5, 6)
		assert len(f.intervalos[0].participantes) == len(f.intervalos[1].participantes) == 3
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		assert float_equal(f.quota(self.m1), 33.333)
		assert float_equal(f.quota(self.m2), 16.667)
		for morador in f.participantes:
			assert float_equal(f.quota(morador), f.quota_peso(morador))
		
		
	def test_calculo_quotas_participantes_3(self):
		'''
		Teste do cálculo da proporção de cada morador. Períodos iguais e sem porcentagem cadastrada
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 20))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 20), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 5, 6))
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 3
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 20)
		assert f.intervalos[1].data_inicial == date(2007, 4, 20) and f.intervalos[1].data_final == date(2007, 4, 21)
		assert f.intervalos[2].data_inicial == date(2007, 4, 21) and f.intervalos[2].data_final == date(2007, 5, 6)
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		assert float_equal(f.intervalos[1].quota(self.m1), 0.833)
		assert float_equal(f.intervalos[2].quota(self.m1), 16.667)
		for morador in f.participantes:
			assert float_equal(f.quota(morador), f.quota_peso(morador))
	
	
	def test_calculo_quotas_participantes_4(self):
		'''
		Teste do cálculo da proporção de cada morador. Um intervalo sem ninguém e sem porcentagem cadastrada
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 20))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 20))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 25), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 4, 30), data_saida = date(2007, 5, 6))
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 4
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 21)
		assert f.intervalos[1].data_inicial == date(2007, 4, 21) and f.intervalos[1].data_final == date(2007, 4, 25)
		assert f.intervalos[2].data_inicial == date(2007, 4, 25) and f.intervalos[2].data_final == date(2007, 4, 30)
		assert f.intervalos[3].data_inicial == date(2007, 4, 30) and f.intervalos[3].data_final == date(2007, 5, 6)
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		assert f.total_dias == 26
		for morador in f.participantes:
			assert float_equal(f.quota(morador), f.quota_peso(morador))
	
	
	def test_calculo_quotas_participantes_5(self):
		'''
		Teste do cálculo da proporção de cada morador. Datas ajustadas para dar 1/5 para um e 2/5 para os outros dois moradores
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 18))
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 2
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 18)
		assert f.intervalos[1].data_inicial == date(2007, 4, 18) and f.intervalos[1].data_final == date(2007, 5, 6)
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		for morador in f.participantes:
			assert float_equal(f.quota(morador), f.quota_peso(morador))
	
	
	def test_calculo_quotas_participantes_peso_1(self):
		'''
		Teste do cálculo da proporção de cada morador. Um intervalo único e COM porcentagem cadastrada dando 100%
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		
		PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m2, peso_quota = Decimal(25), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m3, peso_quota = Decimal(15), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 1
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 5, 6)
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		assert f.total_dias == 30
		for participante in f.participantes:
			assert f.quota(participante) == 25
			assert float_equal(participante.peso_quota(f.data_inicial), f.quota_peso(participante))
	
	
	def test_calculo_quotas_participantes_peso_2(self):
		'''
		Teste do cálculo da proporção de cada morador. Três intervalos e COM porcentagem cadastrada
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 15))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 4, 21), data_saida = date(2007, 5, 6))
		
		PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m2, peso_quota = Decimal(25), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m3, peso_quota = Decimal(15), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 3
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 16)
		assert f.intervalos[1].data_inicial == date(2007, 4, 16) and f.intervalos[1].data_final == date(2007, 4, 21)
		assert f.intervalos[2].data_inicial == date(2007, 4, 21) and f.intervalos[2].data_final == date(2007, 5, 6)
		assert f.intervalos[2].quota_peso(self.m1) == f.intervalos[2].quota_peso(self.m4) == 2 * f.intervalos[2].quota_peso(self.m3)
		assert float_equal(f.quota_peso(self.m1), 2 * f.quota_peso(self.m3))
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
	
	
	def test_calculo_quotas_participantes_peso_3(self):
		'''
		Teste do cálculo da proporção de cada morador. Porcentagem maior que 100%
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 5, 6))
		
		PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m2, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m3, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 1
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 5, 6)
		assert f.quota_peso(self.m1) == f.quota_peso(self.m4) == 20
		assert f.quota_peso(self.m2) == f.quota_peso(self.m3) == 30
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
	
	
	def test_calculo_quotas_participantes_peso_4(self):
		'''
		Teste do cálculo da proporção de cada morador. Um intervalo sem ninguém. Porcentagem maior que 100%
		'''
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 20))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 4, 6), data_saida = date(2007, 4, 20))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 25), data_saida = date(2007, 5, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 4, 30), data_saida = date(2007, 5, 6))
		
		PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m2, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m3, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
		PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
		
		objectstore.flush()
		
		f = self.r.criar_fechamento(date(2007, 5, 6))
		f.calcular_quotas_participantes()
		
		print_calculo_quotas_participantes(f)
		
		assert len(f.intervalos) == 4
		assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 21)
		assert f.intervalos[1].data_inicial == date(2007, 4, 21) and f.intervalos[1].data_final == date(2007, 4, 25)
		assert f.intervalos[2].data_inicial == date(2007, 4, 25) and f.intervalos[2].data_final == date(2007, 4, 30)
		assert f.intervalos[3].data_inicial == date(2007, 4, 30) and f.intervalos[3].data_final == date(2007, 5, 6)
		assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
		assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
		assert f.total_dias == 26

