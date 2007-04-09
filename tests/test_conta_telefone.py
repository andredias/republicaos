#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from tests.base import BaseTest


class TestContaTelefone(BaseTest):
	url = 'postgres://turbo_gears:tgears@localhost/tg_teste'
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
				numero         = 1234,
				periodo_ref    = 200703,
				conta_telefone = c1,
				tipo_fone      = 1,
				tipo_distancia = 1,
				segundos       = 150,
				valor          = Decimal('1.4')
			)
		
		t2 = Telefonema(
				numero         = 3333,
				periodo_ref    = 200704,
				conta_telefone = c1,
				tipo_fone      = 1,
				tipo_distancia = 1,
				segundos       = 299,
				valor          = Decimal('2.15')
			)
		
		t3 = Telefonema(
				numero         = 777,
				periodo_ref    = 200704,
				conta_telefone = c1,
				tipo_fone      = 2,
				tipo_distancia = 1,
				segundos       = 90,
				valor          = Decimal('0.22')
			)
		
		t4 = Telefonema(
				numero         = 777,
				periodo_ref    = 200704,
				conta_telefone = c2,
				tipo_fone      = 2,
				tipo_distancia = 1,
				segundos       = 30,
				valor          = Decimal('0.15')
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
		
		r = Republica(nome = 'Teste',
			data_criacao = date.today(),
			logradouro = 'R. dos Bobos, nº 0')
		
		r2 = Republica(nome = 'Outra República',
			data_criacao = date(2000, 05, 10),
			logradouro = 'R. dos Bobos, nº 1')
		
		Telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = p1, republica = r)
		Telefone(numero = 2222, descricao = 'pizzaria', responsavel = p1, republica = r)
		Telefone(numero = 3333, responsavel = p2, republica = r)
		Telefone(numero = 777, responsavel = p3, republica = r2)
		
		Morador(pessoa = p1, republica = r, data_entrada = date(1998, 02, 01))
		Morador(pessoa = p2, republica = r, data_entrada = date(2005, 10, 13))
		Morador(pessoa = p3, republica = r2, data_entrada = date(2002, 11, 22))
		
		c = ContaTelefone(telefone = 1111, companhia = 1, republica = r)
		
		t1 = Telefonema(
				numero = 1234,
				periodo_ref = 200703,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				segundos = 150,
				valor = Decimal('1.4')
			)
		
		t2 = Telefonema(
				numero = 3333,
				periodo_ref = 200704,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				segundos = 299,
				valor = Decimal('2.15')
			)
		
		t3 = Telefonema(
				numero = 777,
				periodo_ref = 200704,
				conta_telefone = c,
				tipo_fone = 2,
				tipo_distancia = 1,
				segundos = 90,
				valor = Decimal('0.15')
			)
			
		t4 = Telefonema(
				numero = 1234,
				periodo_ref = 200704,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				segundos = 330,
				valor = Decimal('2.5')
			)
		
		objectstore.flush()
		
		c.determinar_responsaveis_telefonemas(2007, 04)
		
		assert t1.responsavel == None
		assert t2.responsavel == p2
		assert t3.responsavel == None
		assert t4.responsavel == p1
	
	
	def test_importacao_conta_telefone_csv(self):
		arq = '''Detalhes da fatura

"Seq       ","Origem                                            ","Descrição                                         ","Periodo/Data             ","Terminal_Destino    ","Local Origem","Local Destino       ","Hora Inicio    ","Hora Fim            ","Imp ","Pais      ","Qtde    ","Unid    ","Valor (R$)          "
"0000001   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","21/10/06 A  99/99/99     ","1234                ","CAS -SP   ","SPO -SP             ","10:28:52       ","                    ","E   ","          ","500     ","MIN     "," 0.59"
"0000002   ","1921212409                                        ","04 - LIGACOES DDD PARA CELULARES                  ","21/10/06 A  99/99/99     ","2222                ","CAS -SP   ","SPO -SP             ","12:57:27       ","                    ","E   ","          ","500     ","MIN     "," 0.27"
"0000003   ","1921212409                                        ","04 - LIGACOES DDI PARA CELULARES                  ","25/10/06 A  99/99/99     ","9999                ","CAS -SP   ","SOC -SP             ","14:32:24       ","                    ","E   ","          ","2600    ","MIN     "," 3.11"
"0000004   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","25/10/06 A  99/99/99     ","1234                ","CAS -SP   ","BRU -SP             ","14:36:15       ","                    ","E   ","          ","2000    ","MIN     "," 2.40"
"0000005   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONES FIXOS         ","99/99/99 A  99/99/99     ","5555                ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","2000    ","MIN     "," 0.20"
"0000006   ","1921212409                                        ","04 - LIGACOES DDD PARA CELULARES                  ","99/99/99 A  99/99/99     ","2222                ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","5000    ","MIN     "," 0.45"
"0000007   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONES FIXOS         ","99/99/99 A  99/99/99     ","5555                ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","10000   ","MIN     "," 0.98"'''

		arq = arq.splitlines()
		
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Felipe')
		p3 = Pessoa(nome = 'Dias')
		
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 03, 06),
			logradouro = 'R. dos Bobos, nº 0')
		
		Telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = p1, republica = r)
		Telefone(numero = 2222, descricao = 'pizzaria', responsavel = p1, republica = r)
		Telefone(numero = 3333, responsavel = p2, republica = r)
		Telefone(numero = 9999, responsavel = p3, republica = r)
		
		Morador(pessoa = p1, republica = r, data_entrada = date(1998, 02, 01), data_saida = date(2006, 12, 01))
		Morador(pessoa = p2, republica = r, data_entrada = date(2006, 02, 01))
		Morador(pessoa = p3, republica = r, data_entrada = date(2007, 01, 11))
		
		c = ContaTelefone(telefone = 2409, companhia = 1, republica = r)
		
		objectstore.flush()
		
		c.importar_csv(arq, tipo = 1, mes = 4, ano = 2007)
		
		t1 = Telefonema.get_by(periodo_ref = 200704, numero = 1234, conta_telefone = c)
		t2 = Telefonema.get_by(periodo_ref = 200704, numero = 2222, conta_telefone = c)
		t3 = Telefonema.get_by(periodo_ref = 200704, numero = 5555, conta_telefone = c)
		t4 = Telefonema.get_by(periodo_ref = 200704, numero = 9999, conta_telefone = c)
		
		assert t1.valor == Decimal('2.99') and t1.segundos == 150 and t1.tipo_fone == 0 and t1.tipo_distancia == 1 and t1.responsavel == p1
		assert t2.valor == Decimal('0.72') and t2.segundos == 330 and t2.tipo_fone == 1 and t2.tipo_distancia == 1 and t2.responsavel == p1
		assert t3.valor == Decimal('1.18') and t3.segundos == 720 and t3.tipo_fone == 0 and t3.tipo_distancia == 0 and t3.responsavel == None
		assert t4.valor == Decimal('3.11') and t4.segundos == 156 and t4.tipo_fone == 1 and t4.tipo_distancia == 2 and t4.responsavel == p3