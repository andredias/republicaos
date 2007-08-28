#!/usr/bin/python
# -*- coding: utf-8 -*-

from republicaos.model.business import *
from elixir import *
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from base import BaseTest


class TestContaTelefone(BaseTest):
	#url = 'postgres://turbo_gears:tgears@localhost/tg_teste'
	
	def test_fechamento_da_conta(self):
		r = Republica(nome = 'Teste',
			data_criacao   = date(2000, 05, 10),
			logradouro     = 'R. dos Bobos, nº 0')
		
		Fechamento(data = date(2007, 06, 10), republica = r)
		Fechamento(data = date(2007, 07, 10), republica = r)
		
		c = ContaTelefone(
				telefone = 2409,
				id_operadora = 1,
				emissao = date(2007, 5, 18),
				vencimento = date(2007, 6, 10),
				franquia = Decimal(30),
				servicos = Decimal(0),
				republica = r
			)
		
		objectstore.flush()
		objectstore.clear()
		
		r = Republica.get_by()
		c = ContaTelefone.get_by()
		
		print 'República: ', r
		for f in r.fechamentos:
			print '\t', f
		print 'Conta Telefone: ', c
		
		assert len(r.fechamentos) == 2
		assert r.fechamento_na_data(c.emissao) == r.fechamentos[-1]
	
	
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
		
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(1998, 02, 01))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2005, 10, 13))
		m3 = Morador(pessoa = p3, republica = r2, data_entrada = date(2002, 11, 22))
		objectstore.flush()
		
		r.registrar_responsavel_telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = m1)
		r.registrar_responsavel_telefone(numero = 2222, descricao = 'pizzaria', responsavel = m1)
		r.registrar_responsavel_telefone(numero = 3333, responsavel = m2)
		r2.registrar_responsavel_telefone(numero = 777, responsavel = m3)
		
		
		c = ContaTelefone(telefone = 1111, id_operadora = 1, emissao = date(2007, 4, 29), vencimento = date(2007, 5, 10), republica = r)
		
		t1 = Telefonema(
				numero = 1234,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				segundos = 150,
				quantia = Decimal('1.4')
			)
		
		t2 = Telefonema(
				numero = 3333,
				conta_telefone = c,
				tipo_fone = 1,
				tipo_distancia = 1,
				segundos = 299,
				quantia = Decimal('2.15')
			)
		
		t3 = Telefonema(
				numero = 777,
				conta_telefone = c,
				tipo_fone = 2,
				tipo_distancia = 1,
				segundos = 90,
				quantia = Decimal('0.15')
			)
		
		
		objectstore.flush()
		
		c.determinar_responsaveis_telefonemas()
		
		assert t1.responsavel is m1
		assert t2.responsavel is m2
		assert t3.responsavel is None

	
	
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
		
		p1 = Pessoa(nome = 'André')
		p2 = Pessoa(nome = 'Felipe')
		p3 = Pessoa(nome = 'Dias')
		
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 3, 6),
			logradouro = 'R. dos Bobos, nº 0')
			
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(1998, 2, 1), data_saida = date(2006, 12, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2006, 2, 1))
		m3 = Morador(pessoa = p3, republica = r, data_entrada = date(2007, 1, 11))
		objectstore.flush()
		
		r.registrar_responsavel_telefone(numero = 1234, descricao = 'tel. do trabalho', responsavel = m1)
		r.registrar_responsavel_telefone(numero = 2222, descricao = 'pizzaria', responsavel = m1)
		r.registrar_responsavel_telefone(numero = 3333, responsavel = m2)
		r.registrar_responsavel_telefone(numero = 9999, responsavel = m3)
		
		c = ContaTelefone(telefone = 2409, id_operadora = 1, emissao = date(2007, 4, 29), vencimento = date(2007, 5, 2), republica = r)
		
		objectstore.flush()
		
		c.importar_csv(arq)
		
		t1 = Telefonema.get_by(numero = 1234, conta_telefone = c)
		t2 = Telefonema.get_by(numero = 2222, conta_telefone = c)
		t3 = Telefonema.get_by(numero = 5555, conta_telefone = c)
		t4 = Telefonema.get_by(numero = 9999, conta_telefone = c)
		
		assert t1.quantia == Decimal('2.99') and t1.segundos == 150 and t1.tipo_fone == 0 and t1.tipo_distancia == 1 and t1.responsavel == m1
		assert t2.quantia == Decimal('0.72') and t2.segundos == 330 and t2.tipo_fone == 1 and t2.tipo_distancia == 1 and t2.responsavel == m1
		assert t3.quantia == Decimal('1.18') and t3.segundos == 720 and t3.tipo_fone == 0 and t3.tipo_distancia == 0 and t3.responsavel == None
		assert t4.quantia == Decimal('3.11') and t4.segundos == 156 and t4.tipo_fone == 1 and t4.tipo_distancia == 2 and t4.responsavel == m3
	
	
	def test_importacao_csv_2(self):
		arq = '''Detalhes da fatura

"Seq       ","Origem                                            ","Descri��o                                         ","Periodo/Data             ","Terminal_Destino    ","Local Origem","Local Destino       ","Hora Inicio    ","Hora Fim            ","Imp ","Pais      ","Qtde    ","Unid    ","Valor (R$)          "
"0000001   ","07/03/29725677                                    ","ENCARGOS POR ATRASO REFERENTE A C.P.S.            ","13/04/07 A  19/04/07     ","                    ","CAS -SP   ","    -               ","               ","                    ","N   ","          ","1000    ","UNID    "," 1.05"
"0000002   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","13/04/07 A  99/99/99     ","1938935899          ","CAS -SP   ","PDA -SP             ","10:02:20       ","                    ","E   ","          ","2500    ","MIN     "," 0.49"
"0000003   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","14/04/07 A  99/99/99     ","1938935899          ","CAS -SP   ","PDA -SP             ","09:58:02       ","                    ","E   ","          ","1100    ","MIN     "," 0.21"
"0000004   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","15/04/07 A  99/99/99     ","1239134306          ","CAS -SP   ","SJC -SP             ","21:01:49       ","                    ","E   ","          ","5600    ","MIN     "," 1.11"
"0000005   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","20/04/07 A  99/99/99     ","1938935899          ","CAS -SP   ","PDA -SP             ","22:56:14       ","                    ","E   ","          ","3600    ","MIN     "," 0.71"
"0000006   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","20/04/07 A  99/99/99     ","1132073274          ","CAS -SP   ","SPO -SP             ","23:00:04       ","                    ","E   ","          ","8300    ","MIN     "," 1.65"
"0000007   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","22/04/07 A  99/99/99     ","1938935899          ","CAS -SP   ","PDA -SP             ","18:18:55       ","                    ","E   ","          ","1400    ","MIN     "," 0.27"
"0000008   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","22/04/07 A  99/99/99     ","1132073274          ","CAS -SP   ","SPO -SP             ","19:09:51       ","                    ","E   ","          ","6100    ","MIN     "," 1.22"
"0000009   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","24/04/07 A  99/99/99     ","7335333394          ","CAS -SP   ","MAS -BA             ","19:43:31       ","                    ","E   ","          ","1000    ","MIN     "," 0.20"
"0000010   ","1921212409                                        ","04 - LIGACOES DDD PARA TELEFONES FIXOS            ","27/04/07 A  99/99/99     ","1239134306          ","CAS -SP   ","SJC -SP             ","10:40:25       ","                    ","E   ","          ","1000    ","MIN     "," 0.20"
"0000011   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA CELULARES               ","20/04/07 A  99/99/99     ","1996338801          ","CAS -SP   ","CAS -SP             ","15:54:58       ","                    ","E   ","          ","1000    ","MIN     "," 0.64"
"0000012   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA NETFONE                 ","99/99/99 A  99/99/99     ","1921212391          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","27000   ","MIN     "," 0.00"
"0000013   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932890813          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","3000    ","MIN     "," 0.29"
"0000014   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932891101          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000015   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932891164          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","12000   ","MIN     "," 1.18"
"0000016   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1933880233          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","2000    ","MIN     "," 0.20"
"0000017   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1935219285          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","2000    ","MIN     "," 0.20"
"0000018   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1940047777          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","10000   ","MIN     "," 1.00"
"0000019   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1934687377          ","CAS -SP   ","AMR -SP             ","               ","                    ","E   ","          ","2000    ","MIN     "," 0.20"
"0000020   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1930320374          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","4000    ","MIN     "," 0.39"
"0000021   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1937498996          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","13000   ","MIN     "," 1.29"
"0000022   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932418046          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","4000    ","MIN     "," 0.39"
"0000023   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932463762          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","3000    ","MIN     "," 0.29"
"0000024   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1921042600          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","5000    ","MIN     "," 0.49"
"0000025   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932730483          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","18000   ","MIN     "," 1.77"
"0000026   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932825430          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000027   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932877719          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000028   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932898912          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000029   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932890432          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000030   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932875607          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000031   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1932720779          ","CAS -SP   ","CAS -SP             ","               ","                    ","E   ","          ","5000    ","MIN     "," 0.49"
"0000032   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1938285430          ","CAS -SP   ","SUM -SP             ","               ","                    ","E   ","          ","7000    ","MIN     "," 0.69"
"0000033   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1938835366          ","CAS -SP   ","SUM -SP             ","               ","                    ","E   ","          ","1000    ","MIN     "," 0.10"
"0000034   ","1921212409                                        ","04 - LIGACOES LOCAIS PARA TELEFONE FIXO  - TOTAIS ","99/99/99 A  99/99/99     ","1938697483          ","CAS -SP   ","VOS -SP             ","               ","                    ","E   ","          ","2000    ","MIN     "," 0.20"
"0000035   ","1921212409                                        ","05 - COMPLEMENTO DE FRANQUIA                      ","12/04/07 A  11/05/07     ","                    ","CAS -SP   ","    -               ","               ","                    ","E   ","          ","1000    ","UNID    "," 18.46"'''

		
		r = Republica(nome = 'Teste',
			data_criacao = date(2007, 3, 6),
			logradouro = 'R. dos Bobos, nº 0')
			
		f = Fechamento(data = date(2007, 6, 6), republica = r)
		
		# TODO: adiciona f à república pq o Elixir não tá fazendo isso
		r.fechamentos.append(f)
			
		p1 = Pessoa(nome = u'André')
		p2 = Pessoa(nome = 'Felipe')
		p3 = Pessoa(nome = 'Dias')
		
		m1 = Morador(pessoa = p1, republica = r, data_entrada = date(1998, 2, 1))
		m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2006, 2, 1))
		m3 = Morador(pessoa = p3, republica = r, data_entrada = date(2007, 1, 11))
		
		c = ContaTelefone(telefone = 2409, id_operadora = 1, emissao = date(2007, 5, 18), vencimento = date(2007, 6, 10), republica = r)
		c.franquia = Decimal('34.93')
		objectstore.flush()
		
		c.importar_csv(arq)
		rateio = c.rateio
		
		from exibicao_resultados import print_rateio_conta_telefone
		print_rateio_conta_telefone(c)
		
		assert c.servicos == Decimal('1.05')
		assert c.total_sem_dono == Decimal('16.47')

