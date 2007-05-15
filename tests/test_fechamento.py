#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import decimal

from model import *
from elixir import *
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from tests.base import BaseTest


class TestFechamentoContas(BaseTest):
	'''
	Testa o fechamento das contas do mês
	'''
	def setup(self):
		BaseTest.setup(self)
		
		self.r = Republica(nome = 'Teste', data_criacao = date(2007, 3, 6), logradouro = 'R. dos Bobos, nº 0')
		
		self.p1 = Pessoa(nome = 'Andre')
		self.p2 = Pessoa(nome = 'Marcos')
		self.p3 = Pessoa(nome = 'Roger')
		self.p4 = Pessoa(nome = 'Leonardo')
		
		self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		self.c = ContaTelefone(
				telefone = 2409,
				companhia = 1,
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
		self.td5 = TipoDespesa(nome = 'Telefone', republica = self.r, especifica = True)
	
	
	def set_despesas(self):
		Despesa(data = Date(2007, 4, 21), valor = 20, tipo_despesa = self.td1, responsavel = self.m1)
		Despesa(data = Date(2007, 4, 19), valor = 100, tipo_despesa = self.td4, responsavel = self.m1)
		Despesa(data = Date(2007, 4, 12), valor = 50, tipo_despesa = self.td3, responsavel = self.m2)
		Despesa(data = Date(2007, 4, 21), valor = 100, tipo_despesa = self.td2, responsavel = self.m1)
		Despesa(data = Date(2007, 5, 1), valor = 100, tipo_despesa = self.td2, responsavel = self.m3)
		Despesa(data = Date(2007, 5, 1), valor = 100, tipo_despesa = self.td2, responsavel = self.m4)
	
	
	def print_acerto_final(self, fechamento):
		write = sys.stdout.write
		write('\n%10s' % ' ')
		for morador in fechamento.moradores:
			write('|%10s' % morador.pessoa.nome)
		write('| Total a Pagar')
		
		a_receber = dict()
		for devedor in fechamento.moradores:
			write('\n%10s' % devedor.pessoa.nome)
			total_a_pagar = Decimal(0)
			if devedor not in fechamento.acerto_a_pagar:
				write(('|%10s' % ' ') * (len(fechamento.moradores) + 1))
			else:
				for credor in fechamento.moradores:
					if credor in fechamento.acerto_a_pagar[devedor]:
						a_pagar           = fechamento.acerto_a_pagar[devedor][credor]
						total_a_pagar    += a_pagar
						a_receber[credor] = a_receber.get(credor, Decimal(0)) + a_pagar
						write('|%10s' % a_pagar)
					else:
						write('|%10s' % ' ')
				write('|%10s' % total_a_pagar)
		write('\n%s' % ('-' * 10 * (len(fechamento.moradores) + 3)))
		write('\n   Receber')
		for credor in fechamento.moradores:
			if credor in a_receber.keys():
				write('|%10s' % a_receber[credor])
			else:
				write('|%10s' % ' ')
		write('\n\n\n')
		sys.stdout.flush()
	
	
	def ajustar_fechamento_para_acerto_final(self, f):
		f.rateio = dict()
		f.rateio[self.m1] = MoradorRateio()
		f.rateio[self.m2] = MoradorRateio()
		f.rateio[self.m3] = MoradorRateio()
		f.rateio[self.m4] = MoradorRateio()
		f.moradores = Set(f.rateio.keys())
	
	
	
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
		
		assert self.m1 not in f.acerto_a_pagar.keys()
		assert self.m3 not in f.acerto_a_pagar.keys()
		assert self.m2 in f.acerto_a_pagar.keys()
		assert self.m4 in f.acerto_a_pagar.keys()
		assert (self.m1 in f.acerto_a_pagar[self.m2]) and f.acerto_a_pagar[self.m2][self.m1] == Decimal('84.00')
		assert (self.m3 in f.acerto_a_pagar[self.m2]) and f.acerto_a_pagar[self.m2][self.m3] == Decimal('82.00')
		assert (self.m3 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m3] == Decimal('72.50')
		
		self.print_acerto_final(f)
	
	
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
		
		assert self.m1 in f.acerto_a_pagar.keys()
		assert self.m2 in f.acerto_a_pagar.keys()
		assert self.m3 in f.acerto_a_pagar.keys()
		assert self.m4 not in f.acerto_a_pagar.keys()
		assert (self.m4 in f.acerto_a_pagar[self.m1]) and f.acerto_a_pagar[self.m1][self.m4] == Decimal(30)
		assert (self.m4 in f.acerto_a_pagar[self.m2]) and f.acerto_a_pagar[self.m2][self.m4] == Decimal(15)
		assert (self.m4 in f.acerto_a_pagar[self.m3]) and f.acerto_a_pagar[self.m3][self.m4] == Decimal(35)
		assert len(f.acerto_a_pagar[self.m1]) == len(f.acerto_a_pagar[self.m2]) == len(f.acerto_a_pagar[self.m3]) == 1
		
		self.print_acerto_final(f)
	
	
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
		
		assert self.m1 not in f.acerto_a_pagar.keys()
		assert self.m2 not in f.acerto_a_pagar.keys()
		assert self.m3 not in f.acerto_a_pagar.keys()
		assert self.m4 in f.acerto_a_pagar.keys() and len(f.acerto_a_pagar) == 1
		assert (self.m1 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m1] == Decimal(30)
		assert (self.m2 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m2] == Decimal(15)
		assert (self.m3 in f.acerto_a_pagar[self.m4]) and f.acerto_a_pagar[self.m4][self.m3] == Decimal(35)
		
		self.print_acerto_final(f)
	
	
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




