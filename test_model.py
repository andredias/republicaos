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
		
	
	def teardown(self):
		# we don't use cleanup_all because setup and teardown are called for 
		# each test, and since the class is not redefined, it will not be
		# reinitialized so we can't kill it
		drop_all()
		objectstore.clear()
	
	
	def test_ultimo_fechamento_contas_vazio(self):
		data_criacao = date.today() - relativedelta(months = 4)
		r = Republica(nome = 'Teste',
			data_criacao = data_criacao,
			logradouro = 'R. dos Bobos, nº 0')
			
		objectstore.flush()
		
		assert (data_criacao, date.today()) == r.ultimo_fechamento()
		assert r.ultimo_fechamento() == r.proximo_fechamento()
		
	def test_fechamento_contas(self):		
		data_criacao = date.today() - relativedelta(months = 4)
		r = Republica(nome = 'Teste',
			data_criacao = data_criacao,
			logradouro = 'R. dos Bobos, nº 0')
		
		for delta in range(1, 4):
			Fechamento(data = (date.today() - relativedelta(months = delta)), republica = r)
		objectstore.flush()
		
		fechamento_anterior1 = date.today() - relativedelta(months = 1)
		fechamento_anterior2 = date.today() - relativedelta(months = 2)
		assert (fechamento_anterior2, fechamento_anterior1) == r.ultimo_fechamento()
		assert (fechamento_anterior1, date.today()) == r.proximo_fechamento()
	
	
	def test_telefonemas_de_conta(self):
		'''
		Teste do método para encontrar os telefonemas do período
		'''
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 03, 06),
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
		
		tels1 = c1.telefonemas(ano = 2007, mes = 03)
		tels2 = c1.telefonemas(2007, 04)
		tels3 = c2.telefonemas(2007, 04)
		
		assert t1 in tels1
		assert t1 not in tels2
		assert t2 in tels2
		assert t3 in tels2
		assert t2 not in tels1
		assert t3 not in tels1
		assert t4 not in tels1
		assert t4 not in tels2
		assert t4 in tels3
	
	
	def test_determinar_responsavel_telefonema(self):
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Felipe')
		p3 = Pessoa(nome = 'Dias')
		
		Telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = p1)
		Telefone(numero = 2222, descricao = 'pizzaria', responsavel = p1)
		Telefone(numero = 3333, responsavel = p2)
		Telefone(numero = 777, responsavel = p3)
		
		r = Republica(nome = 'Teste',
			data_criacao = date.today(),
			logradouro = 'R. dos Bobos, nº 0')
		
		Morador(pessoa = p1, republica = r, data_entrada = date(1998, 02, 01))
		Morador(pessoa = p2, republica = r, data_entrada = date(2005, 10, 13))
		
		c = ContaTelefone(telefone = 2409, companhia = 1, republica = r)
		
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
			
		t4 = Telefonema(
				numero = 1234,
				periodo_ref = 200704,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				duracao = time(0, 5, 30),
				valor = 2.5
			)
		
		
		objectstore.flush()
		
		c.determinar_responsaveis_telefonemas(2007, 04)
		
		assert t1.responsavel == None
		assert t2.responsavel == p2
		assert t3.responsavel == None
		assert t4.responsavel == p1
	
	
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


if __name__ == '__main__':
    teste = TestaModelo()
    teste.setup()
    teste.test_determinar_responsavel_telefonema()
    teste.teardown()
