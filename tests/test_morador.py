#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from datetime import date, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from tests.base import BaseTest

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
		pass
	
	def test_despesas(self):
		pass