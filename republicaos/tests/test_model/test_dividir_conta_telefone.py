#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from datetime   import date, time
from decimal    import Decimal
from dateutil.relativedelta import relativedelta
from republicaos.model import Republica, Fechamento, ContaTelefone, Pessoa, Morador, Telefonema, TelefoneRegistrado
from republicaos.model import TipoDespesa, DespesaPeriodica, Despesa, PesoQuota, Aluguel
from republicaos.tests import Session, TestModel
from exibicao_resultados import print_acerto_final, print_calculo_quotas_participantes
from republicaos.lib.pronus_utils import float_equal

import decimal

decimal.setcontext(decimal.BasicContext)


class TestDividirContaTelefone(TestModel):
    '''
    Testa vários casos de divisão de contas:
    
    SER = serviços adicionais
    TEM = telefonemas de ex-morador
    TSD = telefonemas sem dono
    NDD = número de dias diferentes
    UF  = ultrapassa a franquia
    
    SER | TEM | TSD | NDD | UF | Caso
     0  |  0  |  0  |  0  | 0  |  0
     0  |  0  |  0  |  0  | 1  |  1
     0  |  0  |  0  |  1  | 0  |  2
     0  |  0  |  0  |  1  | 1  |  3
     0  |  0  |  1  |  0  | 0  |  4
     0  |  0  |  1  |  0  | 1  |  5
     0  |  0  |  1  |  1  | 0  |  6
     0  |  0  |  1  |  1  | 1  |  7
     0  |  1  |  0  |  0  | 0  |  8
     0  |  1  |  0  |  0  | 1  |  9
     0  |  1  |  0  |  1  | 0  | 10
     0  |  1  |  0  |  1  | 1  | 11
     0  |  1  |  1  |  0  | 0  | 12
     0  |  1  |  1  |  0  | 1  | 13
     0  |  1  |  1  |  1  | 0  | 14
     0  |  1  |  1  |  1  | 1  | 15
     1  |  0  |  0  |  0  | 0  | 16
     1  |  0  |  0  |  0  | 1  | 17
     1  |  0  |  0  |  1  | 0  | 18
     1  |  0  |  0  |  1  | 1  | 19
     1  |  0  |  1  |  0  | 0  | 20
     1  |  0  |  1  |  0  | 1  | 21
     1  |  0  |  1  |  1  | 0  | 22
     1  |  0  |  1  |  1  | 1  | 23
     1  |  1  |  0  |  0  | 0  | 24
     1  |  1  |  0  |  0  | 1  | 25
     1  |  1  |  0  |  1  | 0  | 26
     1  |  1  |  0  |  1  | 1  | 27
     1  |  1  |  1  |  0  | 0  | 28
     1  |  1  |  1  |  0  | 1  | 29
     1  |  1  |  1  |  1  | 0  | 30
     1  |  1  |  1  |  1  | 1  | 31
    '''
    
    #url = 'postgres://turbo_gears:tgears@localhost/tg_teste'


    def setUp(self):
        TestModel.setUp(self)
        self.r = Republica(nome = 'Teste', data_criacao = date(2007, 3, 6), logradouro = 'R. dos Bobos, nº 0')
        Session.commit()
        self.r.criar_fechamento(data = date(2007, 4, 6))
        self.r.criar_fechamento(data = date(2007, 5, 6))
        
        self.p1 = Pessoa(nome = 'Andre')
        self.p2 = Pessoa(nome = 'Marcos')
        self.p3 = Pessoa(nome = 'Roger')
        self.p4 = Pessoa(nome = 'Leonardo')
        self.p5 = Pessoa(nome = 'Alexandre')
        
        self.c = ContaTelefone(
                telefone = 2409,
                id_operadora = 1,
                emissao = date(2007, 4, 29),
                vencimento = date(2007, 5, 2),
                franquia = Decimal(30),
                servicos = Decimal(0),
                republica = self.r
            )
        
        Session.commit()    
    
    def set_telefones(self, m1, m2, m3, m4 = None, m5 = None):
        self.r.registrar_responsavel_telefone(numero = 10, responsavel = m1)
        self.r.registrar_responsavel_telefone(numero = 11, responsavel = m1)
        self.r.registrar_responsavel_telefone(numero = 20, responsavel = m2)
        self.r.registrar_responsavel_telefone(numero = 21, responsavel = m2)
        self.r.registrar_responsavel_telefone(numero = 30, responsavel = m3)
        self.r.registrar_responsavel_telefone(numero = 31, responsavel = m3)
        if m4:
            self.r.registrar_responsavel_telefone(numero = 40, responsavel = m4)
            self.r.registrar_responsavel_telefone(numero = 41, responsavel = m4)
        if m5:
            self.r.registrar_responsavel_telefone(numero = 50, responsavel = m5)
            self.r.registrar_responsavel_telefone(numero = 51, responsavel = m5)
    
    
    def moradores_numero_dias_iguais(self):
        self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 3, 6))
        Session.commit()
        
        return (self.m1,self.m2, self.m3)
    
    
    def moradores_numero_dias_diferentes(self):
        self.m1 = Morador(pessoa = self.p1, republica = self.r, data_entrada = date(2007, 3, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, data_entrada = date(2007, 3, 6))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, data_entrada = date(2007, 4, 18)) # veja test_fechamento.py:TestFechamento.test_calculo_quotas_participantes_5
        Session.commit()
        
        return (self.m1, self.m2, self.m3)
    
    
    def set_ex_morador(self):
        self.m4 = Morador(pessoa = self.p4, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 4, 4))
        self.m5 = Morador(pessoa = self.p5, republica = self.r, data_entrada = date(2007, 3, 6), data_saida = date(2007, 3, 21))
        Telefonema(numero = 40, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, quantia = Decimal('1.25'))
        Telefonema(numero = 50, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 100, quantia = Decimal('2.50'))
        Session.commit()
        return self.m4, self.m5
    
    
    def ligacoes_dentro_franquia(self):
        Telefonema(numero = 10, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, quantia = Decimal('5.5'))
        Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, quantia = Decimal('2.5'))
        Telefonema(numero = 20, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, quantia = Decimal('4.5'))
        Telefonema(numero = 30, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, quantia = Decimal('5.5'))
    
    
    def ligacoes_ultrapassando_franquia(self):
        Telefonema(numero = 10, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, quantia = Decimal('5.5'))
        Telefonema(numero = 11, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 700, quantia = Decimal(8))
        Telefonema(numero = 20, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 800, quantia = Decimal('4.5'))
        Telefonema(numero = 21, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 800, quantia = Decimal('7.5'))
        Telefonema(numero = 30, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, quantia = Decimal('5.5'))
    
    
    def telefonemas_sem_dono(self):
        t1 = Telefonema(numero = 111, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 1, segundos = 900, quantia = Decimal('2.5'))
        t2 = Telefonema(numero = 222, conta_telefone = self.c, tipo_fone = 1, tipo_distancia = 2, segundos = 900, quantia = Decimal('0.5'))
        return (t1, t2)
    
    
    def executa_caso_xyz(self, servicos, tel_sem_dono, tel_ex_morador, qtd_dias_diferentes, ultrapassa_franquia):
        from exibicao_resultados import print_rateio_conta_telefone
        
        set_morador             = [self.moradores_numero_dias_iguais, self.moradores_numero_dias_diferentes]
        set_ultrapassa_franquia = [self.ligacoes_dentro_franquia , self.ligacoes_ultrapassando_franquia]
        set_telefonema_sem_dono = [None, self.telefonemas_sem_dono]
        set_ex_morador          = [None, self.set_ex_morador]
        
        if servicos:
            self.c.servicos = Decimal(3)
            
        m1, m2, m3 = set_morador[qtd_dias_diferentes]()
        m4 = None
        m5 = None
        if tel_ex_morador:
            m4, m5 = self.set_ex_morador()
            
        self.set_telefones(m1 = m1, m2 = m2, m3 = m3, m4 = m4, m5 = m5)
        set_ultrapassa_franquia[ultrapassa_franquia]()
        
        if tel_sem_dono:
            t1, t2 = self.telefonemas_sem_dono()
    
        Session.commit()
        
#        print 'República: ', self.r
#        for f in self.r.fechamentos:
#            print f
#        print 'Conta Telefone: ', self.c
#        print 'Fechamento: ', self.c.fechamento
        
        self.c.determinar_responsaveis_telefonemas()
        rateio = self.c.rateio
        print_rateio_conta_telefone(self.c)
        
        assert set([m1, m2, m3]) == self.c.moradores
        
        if tel_ex_morador:
            assert set([m4, m5]) == self.c.ex_moradores
            assert float_equal((self.c.fechamento.quota(m4) + self.c.fechamento.quota(m5)), 0.0)
            assert float_equal(sum(rateio.a_pagar(m) for m in [m1, m2, m3, m4, m5]), self.c.total)
            assert self.c.total_ex_moradores == (rateio.telefonemas(m4) + rateio.telefonemas(m5))
        else:
            assert sum(rateio.a_pagar(m) for m in [m1, m2, m3]) == self.c.total
            assert self.c.total_ex_moradores == 0
        
        if ultrapassa_franquia:
            assert self.c.total == (self.c.total_telefonemas + self.c.servicos)
        else:
            assert self.c.total == (self.c.franquia + self.c.servicos)
        
        if qtd_dias_diferentes:
            assert rateio.franquia(m1) == rateio.franquia(m2) == (2 * rateio.franquia(m3))
        else:
            assert rateio.franquia(m1) == rateio.franquia(m2) == rateio.franquia(m3)
            assert float_equal(rateio.franquia(m1), (self.c.franquia + self.c.servicos) / Decimal(3))
        
        if tel_sem_dono:
            assert self.c.total_sem_dono == (t1.quantia + t2.quantia)
        else:
            assert self.c.total_sem_dono == 0
        
    
    
    def test_dividir_conta_caso_00(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  0  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_01(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  0  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
    
    
    
    def test_dividir_conta_caso_02(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  0  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_03(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  0  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
        
        
    def test_dividir_conta_caso_04(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  1  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
        
        
    def test_dividir_conta_caso_05(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  1  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
        assert self.c.rateio.a_pagar(self.m1) == Decimal('12.75')
        assert self.c.rateio.a_pagar(self.m2) == Decimal('11.25')
        
    
    def test_dividir_conta_caso_06(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  1  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_07(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  0  |  1  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_08(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  0  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_09(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  0  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_10(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  0  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_11(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  0  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_12(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  1  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_13(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  1  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_14(self):
        '''
        SER | TEM | TSD | NDD | UF
          0  | 1  |  1  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_15(self):
        '''
        SER | TEM | TSD | NDD | UF
         0  |  1  |  1  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 0, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)


    def test_dividir_conta_caso_16(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  0  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_17(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  0  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
    
    
    
    def test_dividir_conta_caso_18(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  0  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_19(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  0  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
        
        
    def test_dividir_conta_caso_20(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  1  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
        
        
    def test_dividir_conta_caso_21(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  1  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
        assert self.c.rateio.a_pagar(self.m1) == Decimal('13.75')
        assert self.c.rateio.a_pagar(self.m2) == Decimal('12.25')
        
    
    def test_dividir_conta_caso_22(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  1  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_23(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  0  |  1  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 0, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_24(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  0  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_25(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  0  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_26(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  0  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_27(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  0  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 0, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_28(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  1  |  0  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_29(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  1  |  0  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 0, ultrapassa_franquia = 1)
    
    
    def test_dividir_conta_caso_30(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  1  |  1  | 0
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 0)
    
    
    def test_dividir_conta_caso_31(self):
        '''
        SER | TEM | TSD | NDD | UF
         1  |  1  |  1  |  1  | 1
        '''
        self.executa_caso_xyz(servicos = 1, tel_ex_morador = 1, tel_sem_dono = 1, qtd_dias_diferentes = 1, ultrapassa_franquia = 1)

