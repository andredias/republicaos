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


decimal.setcontext(decimal.BasicContext)


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
		
		self.p1 = Pessoa(nome = 'Andre')
		self.p2 = Pessoa(nome = 'Marcos')
		self.p3 = Pessoa(nome = 'Roger')
		self.p4 = Pessoa(nome = 'Leonardo')
		
		self.c = ContaTelefone(
				telefone = 2409,
				companhia = 1,
				emissao = date(2007, 4, 29),
				vencimento = date(2007, 5, 2),
				franquia = Decimal(30),
				servicos = Decimal(0),
				republica = self.r
			)
	
	
	def set_telefones(self, m1, m2, m3, m4 = None):
		Telefone(numero = 11, responsavel = m1)
		Telefone(numero = 22, responsavel = m1)
		Telefone(numero = 33, responsavel = m2)
		Telefone(numero = 44, responsavel = m2)
		Telefone(numero = 55, responsavel = m3)
		Telefone(numero = 66, responsavel = m3)
		if m4:
			Telefone(numero = 77, responsavel = m4)
			Telefone(numero = 88, responsavel = m4)
	
	
	def mostrar_rateio(self, resumo, rateio):
		write = sys.stdout.write
		write('\n\n-------------------------')
		for key, value in resumo.items():
			write('\n%s = %s' % (key, value))
		
		moradores = [(key.pessoa.nome, key) for key in rateio.keys()]
		moradores.sort()
		campos = ('qtd_dias', 'franquia', 'gastos', 'sem_dono', 'excedente', 'servicos', 'a_pagar')
		totais = dict([campo, 0] for campo in campos)
		write('\n\n----------|%9s|%9s|%9s|%9s|%9s|%9s|%9s' % campos)
		for nome, morador in moradores:
			write('\n%10s' % nome)
			for campo in campos:
				write('|%9s' % rateio[morador][campo])
				totais[campo] += rateio[morador][campo]
		
		# mostra totais
		write('\n----------')
		for campo in campos:
			write('|%9s' % totais[campo])
		write('\n\n')
	
	
	def moradores_numero_dias_iguais(self):
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
		
		return (m1, m2, m3)
	
	
	def moradores_numero_dias_diferentes(self):
		m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
		m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
		m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 21)) # entrou no meio do período
		
		return (m1, m2, m3)
	
	
	def set_ex_morador(self):
		m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
		Telefonema(numero = 77, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, valor = Decimal('1.25'))
		return m4
	
	
	def ligacoes_dentro_franquia(self):
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
	
	
	def ligacoes_ultrapassando_franquia(self):
		Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
		Telefonema(numero = 22, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, valor = Decimal('10.5'))
		Telefonema(numero = 33, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, valor = Decimal('4.5'))
		Telefonema(numero = 44, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, valor = Decimal('7.5'))
		Telefonema(numero = 55, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('5.5'))
	
	
	def telefonemas_sem_dono(self):
		t1 = Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, valor = Decimal('2.5'))
		t2 = Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, valor = Decimal('0.5'))
		return (t1, t2)
	
	
	def executa_caso_xyz(self, qtd_dias_diferentes, ultrapassa_franquia, tel_sem_dono, tel_ex_morador):
		set_morador             = [self.moradores_numero_dias_iguais, self.moradores_numero_dias_diferentes]
		set_ultrapassa_franquia = [self.ligacoes_dentro_franquia , self.ligacoes_ultrapassando_franquia]
		set_telefonema_sem_dono = [None, self.telefonemas_sem_dono]
		set_ex_morador          = [None, self.set_ex_morador]
		
		m1, m2, m3 = set_morador[qtd_dias_diferentes]()
		m4 = None
		if tel_ex_morador:
			m4 = self.set_ex_morador()
			
		self.set_telefones(m1 = m1, m2 = m2, m3 = m3, m4 = m4)
		set_ultrapassa_franquia[ultrapassa_franquia]()
		
		if tel_sem_dono:
			t1, t2 = self.telefonemas_sem_dono()
	
		objectstore.flush()
		
		self.c.determinar_responsaveis_telefonemas()
		resumo, rateio = self.c.dividir_conta()
		self.mostrar_rateio(resumo, rateio)
		
		if tel_ex_morador:
			assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar'] + rateio[m4]['a_pagar']) == resumo['total_conta']
			assert resumo['total_ex_moradores'] == rateio[m4]['gastos']
		else:
			assert (rateio[m1]['a_pagar'] + rateio[m2]['a_pagar'] + rateio[m3]['a_pagar']) == resumo['total_conta']
			assert resumo['total_ex_moradores'] == 0
		
		if ultrapassa_franquia:
			assert resumo['total_conta'] == (resumo['total_telefonemas'] + self.c.servicos)
		else:
			assert resumo['total_conta'] == (self.c.franquia + self.c.servicos)
		
		if qtd_dias_diferentes:
			assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == (2 * rateio[m3]['franquia'])
		else:
			assert rateio[m1]['franquia'] == rateio[m2]['franquia'] == rateio[m3]['franquia'] == (self.c.franquia / 3)
		
		if tel_sem_dono:
			assert resumo['total_sem_dono'] == (t1.valor + t2.valor)
		else:
			assert resumo['total_sem_dono'] == 0
	
	
	def test_dividir_conta_caso_0(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  0  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_01(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  0  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
	
	
	
	def test_dividir_conta_caso_02(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  1  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_03(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  0  |  1  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
		
		
	def test_dividir_conta_caso_04(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  0  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
		
		
	def test_dividir_conta_caso_05(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  0  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
	
	
	def test_dividir_conta_caso_06(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  1  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_07(self):
		'''
		TEM | TSD | NDD | UF
		 0  |  1  |  1  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
	
	
	def test_dividir_conta_caso_08(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  0  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_09(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  0  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
	
	
	def test_dividir_conta_caso_10(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  1  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_11(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  0  |  1  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
	
	
	def test_dividir_conta_caso_12(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  0  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_13(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  0  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
	
	
	def test_dividir_conta_caso_14(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  1  | 0
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
	
	
	def test_dividir_conta_caso_15(self):
		'''
		TEM | TSD | NDD | UF
		 1  |  1  |  1  | 1
		'''
		self.executa_caso_xyz(tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)


