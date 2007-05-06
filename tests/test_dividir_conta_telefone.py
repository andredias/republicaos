#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from model import *
from elixir import *
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from tests.base import BaseTest

class TestDividirContaTelefone(BaseTest):
	'''
	Testa vários casos de divisão de contas:
	
	TEM = telefonemas de ex-morador
	TSD = telefonemas sem dono
	NDD = número de dias diferentes
	UF  = ultrapassa a franquia
	
	TEM | TSD | NDD | UF | Caso
	 0  |  0  |  0  | 0  |  0
	 0  |  0  |  0  | 1  |  1
	 0  |  0  |  1  | 0  |  2
	 0  |  0  |  1  | 1  |  3
	 0  |  1  |  0  | 0  |  4
	 0  |  1  |  0  | 1  |  5
	 0  |  1  |  1  | 0  |  6
	 0  |  1  |  1  | 1  |  7
	 1  |  0  |  0  | 0  |  8
	 1  |  0  |  0  | 1  |  9
	 1  |  0  |  1  | 0  | 10
	 1  |  0  |  1  | 1  | 11
	 1  |  1  |  0  | 0  | 12
	 1  |  1  |  0  | 1  | 13
	 1  |  1  |  1  | 0  | 14
	 1  |  1  |  1  | 1  | 15
	'''
	
	url = 'postgres://turbo_gears:tgears@localhost/tg_teste'

	def setup(self):
		BaseTest.setup(self)
		
		self.r = Republica(nome = 'Teste', data_criacao = date(2007, 3, 6), logradouro = 'R. dos Bobos, nº 0')
		
		Fechamento(republica = self.r, data = date(2007, 4, 6))
		Fechamento(republica = self.r, data = date(2007, 5, 6))
		
		self.p1 = Pessoa(nome = 'André')
		self.p2 = Pessoa(nome = 'Marcos')
		self.p3 = Pessoa(nome = 'Roger')
		self.p4 = Pessoa(nome = 'Leonardo')
		
		Telefone(numero = 11, responsavel = self.p1, republica = self.r)
		Telefone(numero = 22, responsavel = self.p1, republica = self.r)
		Telefone(numero = 33, responsavel = self.p2, republica = self.r)
		Telefone(numero = 44, responsavel = self.p2, republica = self.r)
		Telefone(numero = 55, responsavel = self.p3, republica = self.r)
		Telefone(numero = 66, responsavel = self.p3, republica = self.r)
		Telefone(numero = 77, responsavel = self.p4, republica = self.r)
		Telefone(numero = 88, responsavel = self.p4, republica = self.r)
	
		self.c = ContaTelefone(
				telefone = 2409,
				companhia = 1,
				emissao = date(2007, 4, 29),
				vencimento = date(2007, 5, 2),
				franquia = Decimal(30),
				servicos = Decimal(0),
				republica = self.r
			)
	
	
	def mostrar_rateio(self, rateio):
		write = sys.stderr.write
		write('\n\n-------------------------')
		for key, value in rateio.iteritems():
			if type(value) is not dict:
				write('\n%s = %s' % (key, value))
			else:
				write('\n%s\n-------' % (key.pessoa.nome))
				for k, v in value.iteritems():
					write('\n\t%s = %s' % (k, v))
		write('\n\n')
	
	
	def test_dividir_conta_caso_0(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  0  | 0
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_telefonemas'] == Decimal('15.5')
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == 0		
		assert rateio[m1]['a_pagar'] == rateio[m2]['a_pagar'] == rateio[m3]['a_pagar'] == Decimal(10)
		assert rateio[m1]['excedente'] == rateio[m2]['excedente'] == rateio[m3]['excedente'] == 0
	
	
	def test_dividir_conta_caso_01(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  0  | 1
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas'] == Decimal('33.5')
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == 0		
		assert rateio[m3]['a_pagar'] == Decimal(10)
		assert rateio[m1]['excedente'] == Decimal(6)
		assert rateio[m2]['excedente'] == Decimal(2)
	
	
	def test_dividir_conta_caso_02(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  1  | 0
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_telefonemas'] == Decimal('15.5')
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == 0
		assert rateio[m1]['excedente'] == rateio[m2]['excedente'] == rateio[m3]['excedente'] == 0
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
	
	
	def test_dividir_conta_caso_03(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  1  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas'] == Decimal('33.5')
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == 0
		
		
	def test_dividir_conta_caso_04(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  0  | 0
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		# Telefonemas sem dono
		Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_sem_dono'] == Decimal(3)
		assert rateio['total_ex_moradores'] == 0
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == rateio[m3]['franquia'] == (self.c.franquia / 3)
		
		
	def test_dividir_conta_caso_05(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  0  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		# Telefonemas sem dono
		Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas'] == Decimal('36.5')
		assert rateio['total_sem_dono'] == Decimal(3)
		assert rateio['total_ex_moradores'] == 0
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == rateio[m3]['franquia'] == (self.c.franquia / 3)
	
	
	def test_dividir_conta_caso_06(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  1  | 0
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		# Telefonemas sem dono
		Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_sem_dono'] == Decimal(3)
		assert rateio['total_ex_moradores'] == 0
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
	
	
	def test_dividir_conta_caso_07(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  1  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		# Telefonemas sem dono
		Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas']
		assert rateio['total_sem_dono'] == Decimal(3)
		assert rateio['total_ex_moradores'] == 0
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
	
	
	def test_dividir_conta_caso_08(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  0  | 0
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('5'))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('1.25'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_telefonemas'] == Decimal('16.25')
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == Decimal('1.25')
		assert rateio[m1]['a_pagar'] == rateio[m2]['a_pagar'] == rateio[m3]['a_pagar'] == Decimal(10)
		assert rateio[m1]['excedente'] == rateio[m2]['excedente'] == rateio[m3]['excedente'] == 0
	
	
	def test_dividir_conta_caso_09(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  0  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas']
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == rateio[m4]['gastos']
	
	
	def test_dividir_conta_caso_10(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  1  | 0
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_telefonemas'] == Decimal('18')
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == rateio[m4]['gastos']
		assert rateio[m1]['excedente'] == rateio[m2]['excedente'] == rateio[m3]['excedente'] == 0
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
	
	
	def test_dividir_conta_caso_11(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  1  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas']
		assert rateio['total_sem_dono'] == 0
		assert rateio['total_ex_moradores'] == Decimal('2.5')
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
	
	
	def test_dividir_conta_caso_12(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  0  | 0
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2.5'))
		
		# Telefonemas sem dono
		Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_sem_dono'] == Decimal(3)
		assert rateio['total_ex_moradores'] == Decimal('2.5')
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == rateio[m3]['franquia'] == (self.c.franquia / 3)
	
	
	def test_dividir_conta_caso_13(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  0  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2.5'))
		
		# Telefonemas sem dono
		t1 = Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		t2 = Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas']
		assert rateio['total_sem_dono'] == (t1.valor + t2.valor)
		assert rateio['total_ex_moradores'] == rateio[m4]['gastos']
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == rateio[m3]['franquia'] == (self.c.franquia / 3)
	
	
	def test_dividir_conta_caso_14(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  1  | 0
		'''
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2.5'))
		
		# Telefonemas sem dono
		t1 = Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		t2 = Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == self.c.franquia
		assert rateio['total_sem_dono'] == (t1.valor + t2.valor)
		assert rateio['total_ex_moradores'] == rateio[m4]['gastos']
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
	
	
	def test_dividir_conta_caso_15(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  1  | 1
		'''
		
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('2.5'))
		
		# Telefonemas sem dono
		t1 = Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		t2 = Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		rateio = self.c.dividir_conta()
		self.mostrar_rateio(rateio)
		
		assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == rateio['total_conta']
		assert rateio['total_conta'] == rateio['total_telefonemas'] == Decimal(39)
		assert rateio['total_sem_dono'] == (t1.valor + t2.valor)
		assert rateio['total_ex_moradores'] == rateio[m4]['gastos']
		assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia']) == Decimal(12)


