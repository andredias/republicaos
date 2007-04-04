#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from datetime import date
from dateutil.relativedelta import relativedelta

def setup():
	metadata.connect('sqlite:///')
	metadata.engine.echo = True
	create_all()
	p1 = Pessoa(nome = 'André')
	p2 = Pessoa(nome = 'Marcos')
	
	t1 = Telefone(numero = 1932730483, descricao = 'Casa da Andréa')
	t2 = Telefone(numero = 1996338801, descricao = 'Celular da Andréa')
	t3 = Telefone(numero = 1239134306, descricao = 'Casa dos pais')
	
	t1.responsavel = p1
	t2.responsavel = p1
	t3.responsavel = p2
	
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
	
	ContaTelefone(telefone = 1921212409, companhia = 1, republica = r)
	ContaTelefone(telefone = 1932899401, companhia = 2, republica = r)
	objectstore.flush()

def teardown():
	cleanup_all()


class TestaModelo(object):
	#def teardown(self):
		## we don't use cleanup_all because setup and teardown are called for 
		## each test, and since the class is not redefined, it will not be
		## reinitialized so we can't kill it
		#drop_all()


	def test_responsavel_por_telefonemas(self):
		p1 = Pessoa.get_by(nome = 'André')
		
		t = Telefone.get_by(numero = 1932730483)
		assert t.responsavel is p1
		
		t = Telefone.get_by(numero = 1996338801)
		assert t.responsavel is p1
		
		t = Telefone.get_by(numero = 1239134306)
		assert not t.responsavel is p1


	def test_moradores(self):
		r = Republica.get_by(nome = 'Jerônimo')
		m = r.moradores(date(2007, 03, 02))
		
		assert Pessoa.get_by(nome = 'André') in m
		assert Pessoa.get_by(nome = 'Marcos') in m


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


	def test_conta_telefone(self):
		r = Republica.get_by(id = 1)
		c = ContaTelefone(telefone = 1921212409, companhia = 1, republica = r)
		

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
		
		pass