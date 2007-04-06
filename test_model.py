#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from datetime import date, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine

#def setup():
	#metadata.connect('sqlite:///')
	#metadata.engine.echo = True
	#metadata.create_all()


#def teardown():
	#cleanup_all()


class TestaModelo(object):
	def setup(self):
		#metadata.connect('postgres://turbo_gears:tgears@localhost/tg_teste')
		metadata.connect('sqlite:///')
		metadata.engine.echo = True
		create_all()
		
	
	def massa_teste_1(self):
		objectstore.clear()
		
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Marcos')
		
		t1 = Telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = p1)
		t2 = Telefone(numero = 4444, descricao = 'Celular do Fulano', responsavel = p1)
		t3 = Telefone(numero = 5555, descricao = 'Casa dos pais', responsavel = p2)
		
		r = Republica(nome = 'Jerônimo',
					data_criacao = date(year = 1998, month = 02, day = 01),
					logradouro = 'R. Jerônimo Pattaro, 186',
					bairro = 'Barão Geraldo',
					cidade = 'Campinas',
					uf = 'SP',
					cep = '13084110')
		
		Morador(
			pessoa = p1,
			republica = r,
			data_entrada = date(1998, 02, 01)
		)
	
		Morador(
			pessoa = p2,
			republica = r,
			data_entrada = date(2005, 10, 13)
		)
		
		ContaTelefone(telefone = 2409, companhia = 1, republica = r)
		objectstore.flush()

	
	def teardown(self):
		# we don't use cleanup_all because setup and teardown are called for 
		# each test, and since the class is not redefined, it will not be
		# reinitialized so we can't kill it
		drop_all()
		objectstore.clear()


	def test_ultimo_fechamento_contas(self):
		r = Republica(nome = 'Teste',
			data_criacao = date.today(),
			logradouro = 'R. dos Bobos, nº 0')
			
		objectstore.flush()
		
		assert date.today() == r.ultimo_fechamento()
		
		for delta in range(1, 4):
			Fechamento(data = (date.today() - relativedelta(months = delta)), republica = r)
		objectstore.flush()
		
		data_fechamento = date.today() - relativedelta(months = 1)
		assert data_fechamento == r.ultimo_fechamento()


	def test_telefonemas_de_conta(self):
		'''
		Testa o método da classe ContaTelefone para encontrar os telefonemas do período
		'''
		r = Republica(nome = 'Teste',
			data_criacao = date.today(),
			logradouro = 'R. dos Bobos, nº 0')
		
		c1 = ContaTelefone(telefone = 2409, companhia = 1, republica = r)
		c2 = ContaTelefone(telefone = 2121, companhia = 2, republica = r)
		
		t1 = Telefonema(
				numero = 1234,
				periodo_ref = 200703,
				conta_telefone = c1,
				tipo_fone = 1,
				tipo_distancia = 1,
				duracao = time(0, 2, 30),
				valor = 1.4
			)
		
		t2 = Telefonema(
				numero = 3333,
				periodo_ref = 200704,
				conta_telefone = c1,
				tipo_fone = 1,
				tipo_distancia = 1,
				duracao = time(0, 4, 59),
				valor = 2.15
			)
		
		t3 = Telefonema(
				numero = 777,
				periodo_ref = 200704,
				conta_telefone = c1,
				tipo_fone = 2,
				tipo_distancia = 1,
				duracao = time(0, 1, 30),
				valor = 0.15
			)
		
		t4 = Telefonema(
				numero = 777,
				periodo_ref = 200704,
				conta_telefone = c2,
				tipo_fone = 2,
				tipo_distancia = 1,
				duracao = time(0, 0, 30),
				valor = 0.15
			)
		
		objectstore.flush()
		
		tels1 = c1.telefonemas(date(2007, 03, 01))
		tels2 = c1.telefonemas(date(2007, 04, 01))
		
		assert t1 in tels1
		assert t1 not in tels2
		assert t2 in tels2
		assert t3 in tels2
		assert t2 not in tels1
		assert t3 not in tels1
		assert t4 not in tels2
		assert t4 not in tels1


	def test_determinar_responsavel_telefonema(self):
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Felipe')
		
		Telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = p1)
		Telefone(numero = 2222, descricao = 'pizzaria', responsavel = p1)
		Telefone(numero = 3333, responsavel = p2)
		
		r = Republica(nome = 'Teste',
			data_criacao = date.today(),
			logradouro = 'R. dos Bobos, nº 0')
		
		Morador(pessoa = p1, republica = r, data_entrada = date(1998, 02, 01))
		Morador(pessoa = p2, republica = r, data_entrada = date(2005, 10, 13))
		
		c = ContaTelefone(telefone = 2409, companhia = 1, republica = r)
		
		objectstore.flush()
		
		t1 = Telefonema(
				numero = 1234,
				periodo_ref = 200703,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				duracao = time(0, 2, 30),
				valor = 1.4
			)
		
		t2 = Telefonema(
				numero = 3333,
				periodo_ref = 200704,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				duracao = time(0, 4, 59),
				valor = 2.15
			)
		
		t3 = Telefonema(
				numero = 777,
				periodo_ref = 200704,
				conta_telefone = c,
				tipo_fone = 2,
				tipo_distancia = 1,
				duracao = time(0, 1, 30),
				valor = 0.15
			)
		
		c.encontrar_responsaveis_telefonemas()
		
		objectstore.flush()
		
		assert True


	def test_conta_telefone(self):
		r = Republica(nome = 'Jerônimo',
					data_criacao = date(year = 1998, month = 02, day = 01),
					logradouro = 'R. Jerônimo Pattaro, 186',
					bairro = 'Barão Geraldo',
					cidade = 'Campinas',
					uf = 'SP',
					cep = '13084110')
		c = ContaTelefone(telefone = 2121, companhia = 2, republica = r)
		
		objectstore.flush()

		assert True
		
		

	def test_importacao_conta_telefone_csv(self):
		csv = '''Detalhes da fatura

"Seq       ","Origem                                            ","Descrição                                         ","Periodo/Data             ","Terminal_Destino    ","Local Origem","Local Destino       ","Hora Inicio    ","Hora Fim            ","Imp ","Pais      ","Qtde    ","Unid    ","Valor (R$)          "
"0000001   ","1921212409                                        ","04 - LIGACOES DDD PARA CELULARES                  ","21/10/06 A  99/99/99     ","1199999999          ","CAS -SP   ","SPO -SP             ","10:28:52       ","                    ","E   ","          ","500     ","MIN     "," 0.59"
"0000002   ","1921212409                                        ","04 - LIGACOES DDD PARA CELULARES                  ","21/10/06 A  99/99/99     ","1199999991          ","CAS -SP   ","SPO -SP             ","12:57:27       ","                    ","E   ","          ","500     ","MIN     "," 0.59"
"0000003   ","1921212409                                        ","04 - LIGACOES DDD PARA CELULARES                  ","25/10/06 A  99/99/99     ","1599999999          ","CAS -SP   ","SOC -SP             ","14:32:24       ","                    ","E   ","          ","2600    ","MIN     "," 3.11"
"0000004   ","1921212409                                        ","04 - LIGACOES DDD PARA CELULARES                  ","25/10/06 A  99/99/99     ","1499999992          ","CAS -SP   ","BRU -SP             ","14:36:15       ","                    ","E   ","          ","2000    ","MIN     "," 2.40"
"0000005   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONES FIXOS         ","99/99/99 A  99/99/99     ","1932222222          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","2000    ","MIN     "," 0.20"
"0000006   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONES FIXOS         ","99/99/99 A  99/99/99     ","1933333333          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","5000    ","MIN     "," 0.49"
"0000007   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONES FIXOS         ","99/99/99 A  99/99/99     ","1944444444          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","10000   ","MIN     "," 0.98"'''

		csv = csv.splitlines()
		assert True