#!/usr/bin/python
# -*- coding: utf-8 -*-

from republicaos.model.business import *
from elixir import *
from datetime import date, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from base import BaseTest



class TestRepublica(BaseTest):
	def test_criar_fechamento(self):
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 4, 8),
			logradouro = 'R. dos Bobos, nº 0')
		
		objectstore.flush()
		
		r.criar_fechamento()
		assert len(r.fechamentos) == 1
		assert r.fechamentos[0].data == date(2007, 5, 8)
		
		r.criar_fechamento()
		assert len(r.fechamentos) == 2
		assert r.fechamentos[0].data == date(2007, 6, 8)
		
		r.criar_fechamento(data = date(2007, 5, 15))
		assert len(r.fechamentos) == 3
		assert r.fechamentos[1].data == date(2007, 5, 15)
		
		r.criar_fechamento(data = date(2007, 7, 10))
		assert len(r.fechamentos) == 4
		assert r.fechamentos[0].data == date(2007, 7, 10)
		
		
	def test_fechamento_na_data(self):
		'''
		Testa se o próximo fechamento está no intervalo correto.
		
		O intervalo esperado é [data_ultimo_periodo_fechamento, data_ultimo_periodo_fechamento + 1 mês - 1 dia] ou escrito de outra forma
		[data_ultimo_periodo_fechamento, data_ultimo_periodo_fechamento + 1 mês[
		'''
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 4, 8),
			logradouro = 'R. dos Bobos, nº 0')
		
		objectstore.flush()
		
		assert r.fechamento_na_data(date(2007, 4, 8)) is None
		
		
		Fechamento(data = date(2007, 5, 10), republica = r)
		objectstore.flush()
		objectstore.clear()
		r = Republica.get_by()
		
		assert r.fechamento_na_data(date(2007, 4, 8))  == r.fechamentos[-1]
		
		Fechamento(data = date(2007, 6, 10), republica = r)
		Fechamento(data = date(2007, 7, 10), republica = r)
		objectstore.flush()
		objectstore.clear()
		r = Republica.get_by()
		
		print '\nrepública = ', r
		for fechamento in r.fechamentos:
			print fechamento
		
		assert len(r.fechamentos) == 3
		for i in range(len(r.fechamentos) - 1):
			assert r.fechamentos[i].data_inicial == r.fechamentos[i + 1].data
			assert r.fechamentos[i].data_final   == (r.fechamentos[i].data - relativedelta(days = 1))
			
		assert r.fechamento_na_data(date(2007, 5, 9))  == r.fechamentos[-1]
		assert r.fechamento_na_data(date(2007, 5, 10)) == r.fechamentos[-2]
		assert r.fechamento_na_data(date(2007, 6, 9))  == r.fechamentos[-2]
		assert r.fechamento_na_data(date(2007, 6, 10)) == r.fechamentos[0]
		assert r.fechamento_na_data(date(2007, 7, 10)) is None
		
	
	
	def test_contas_telefone(self):
		r1 = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), logradouro = 'R. dos Bobos, nº 0')
		r2 = Republica(nome = 'Teste2', data_criacao = date(2007, 5, 8), logradouro = 'R. dos Bobos, nº 1')
		
		c1 = ContaTelefone(telefone = 11, id_operadora = 1, emissao = date(2007, 4, 29), vencimento = date(2007, 5, 10), republica = r1)
		c2 = ContaTelefone(telefone = 11, id_operadora = 2, emissao = date(2007, 5, 29), vencimento = date(2007, 5, 10), republica = r1)
		c3 = ContaTelefone(telefone = 11, id_operadora = 2, emissao = date(2007, 6, 21), vencimento = date(2007, 5, 10), republica = r1)
		c4 = ContaTelefone(telefone = 22, id_operadora = 1, emissao = date(2007, 4, 29), vencimento = date(2007, 5, 10), republica = r2)
		c5 = ContaTelefone(telefone = 22, id_operadora = 1, emissao = date(2007, 5, 10), vencimento = date(2007, 5, 10), republica = r2)
		
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
		
		Casos de apuração:
		
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
	
	
	def test_registrar_responsavel_telefone(self):
		r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), logradouro = 'R. dos Bobos, nº 0')
		
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Marcos')
	
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 2, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 3, 20))
		objectstore.flush()
		
		r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
		r.registrar_responsavel_telefone(numero = 222, responsavel = m2)
		r.registrar_responsavel_telefone(numero = 333, responsavel = m2)
		objectstore.clear()
		
		r  = Republica.get_by(id = 1)
		m1 = Morador.get_by(id_pessoa = 1)
		m2 = Morador.get_by(id_pessoa = 2)
		t1 = TelefoneRegistrado.get_by(numero = 111, republica = r)
		t2 = TelefoneRegistrado.get_by(numero = 222, republica = r)
		t3 = TelefoneRegistrado.get_by(numero = 333, republica = r)
		
		assert t1 is not None
		assert t2 is not None
		assert t3 is not None
		assert t1.responsavel is m1
		assert t2.responsavel is m2
		assert t3.responsavel is m2
		
		r.registrar_responsavel_telefone(numero = 333, responsavel = m1)
		r.registrar_responsavel_telefone(numero = 111, responsavel = None)
		r.registrar_responsavel_telefone(numero = 777, responsavel = None)
		objectstore.clear()
	
		r  = Republica.get_by(id = 1)
		m1 = Morador.get_by(id_pessoa = 1)
		m2 = Morador.get_by(id_pessoa = 2)
		t1 = TelefoneRegistrado.get_by(numero = 111, republica = r)
		t2 = TelefoneRegistrado.get_by(numero = 222, republica = r)
		t3 = TelefoneRegistrado.get_by(numero = 333, republica = r)
		t4 = TelefoneRegistrado.get_by(numero = 777, republica = r)
		
		assert t1 is None
		assert t2.responsavel is m2
		assert t3.responsavel is m1
		assert t4 is None
	
	
	def test_registrar_responsavel_telefone_2(self):
		'''
		Testa um problema que parece ser do Elixir para atulizar automaticamente uma lista de dependências entre uma 
		entidade e outra de uma relação has_many/one_to_many.
		
		Não tenho certeza se a adição à lista deveria acontecer automaticamente.
		veja o post publicado no grupo do sqlelixir:
		http://groups.google.com/group/sqlelixir/browse_thread/thread/710e82c3ad586aab/03fc48b416a09fcf#03fc48b416a09fcf
		'''
		r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), logradouro = 'R. dos Bobos, nº 0')
		
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Marcos')
	
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 2, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 3, 20))
		objectstore.flush()
		
		r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
		try:
			r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
			r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
		except:
			assert False, 'Erro no registro do mesmo responsável repetidamente'
		
		r.registrar_responsavel_telefone(numero = 777, responsavel = m1)
		r.registrar_responsavel_telefone(numero = 777, responsavel = None)
		
		assert TelefoneRegistrado.get_by(numero = 777, republica = r) is None
	
	
	def test_registrar_responsavel_telefone_3(self):
		'''
		Segue a mesma linha do teste 2
		'''
		r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), logradouro = 'R. dos Bobos, nº 0')
		
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Marcos')
	
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 2, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 3, 20))
		objectstore.flush()
		
		r.registrar_responsavel_telefone(numero = 777, responsavel = m1)
		r.registrar_responsavel_telefone(numero = 777, responsavel = None)
		
		assert TelefoneRegistrado.get_by(numero = 777, republica = r) is None

