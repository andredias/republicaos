#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from datetime   import date, time
from decimal    import Decimal
from dateutil.relativedelta import relativedelta
from republicaos.model import Republica, Fechamento, ContaTelefone, Pessoa, Morador, Telefonema, TelefoneRegistrado
from republicaos.model import TipoDespesa, DespesaPeriodica, Despesa, PesoQuota
from republicaos.tests import Session, TestModel

class TestMorador(TestModel):
    def test_qts_dias_morados(self):
        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 4, 8),
            logradouro = 'R. dos Bobos, nº 0')
        p = Pessoa(nome = 'André')
        m = Morador(pessoa = p, republica = r, data_entrada = date(2007, 5, 8), data_saida = date(2007, 6, 10))
        
        Session.commit()
        
        assert m.qtd_dias_morados(date(2007, 4, 8), date(2007, 5, 7)) == 0
        assert m.qtd_dias_morados(date(2007, 5, 8), date(2007, 6, 7)) == 31
        assert m.qtd_dias_morados(date(2007, 6, 8), date(2007, 7, 7)) == 3
        assert m.qtd_dias_morados(date(2007, 7, 8), date(2007, 8, 7)) == 0
    
    
    
    def test_telefonemas(self):
        p1 = Pessoa(nome = 'André')
        
        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 3, 6),
            logradouro = 'R. dos Bobos, nº 0')
        
        m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 3, 6), data_saida = date(2006, 12, 1))
        
        TelefoneRegistrado(numero = 1234, descricao = 'tel. do trabalho', republica = r, responsavel = m1)
        TelefoneRegistrado(numero = 2222, descricao = 'pizzaria', republica = r, responsavel = m1)
        
        c1 = ContaTelefone(telefone = 2409, operadora_id = 1, emissao = date(2007, 4, 19), vencimento = date(2007, 5, 2), republica = r)
        c2 = ContaTelefone(telefone = 2409, operadora_id = 1, emissao = date(2007, 5, 18), vencimento = date(2007, 6, 6), republica = r)
        
        t1 = Telefonema(numero = 1234, conta_telefone = c1, tipo_fone = 1, tipo_distancia = 1, segundos = 150, quantia = 1.4)
        t2 = Telefonema(numero = 3333, conta_telefone = c1, tipo_fone = 1, tipo_distancia = 1, segundos = 299, quantia = 2.15)
        t3 = Telefonema(numero = 2222, conta_telefone = c1, tipo_fone = 1, tipo_distancia = 1, segundos = 200, quantia = 4.0)
        t4 = Telefonema(numero = 2222, conta_telefone = c2, tipo_fone = 1, tipo_distancia = 1, segundos = 300, quantia = 2.5)
        t5 = Telefonema(numero = 7777, conta_telefone = c2, tipo_fone = 1, tipo_distancia = 1, segundos = 60,  quantia = 0.10)
        
        Session.commit()
        
        c1.determinar_responsaveis_telefonemas()
        c2.determinar_responsaveis_telefonemas()
        
        telefonemas_c1 = m1.telefonemas(c1)
        telefonemas_c2 = m1.telefonemas(c2)
        
        assert t1 in telefonemas_c1
        assert t1 not in telefonemas_c2
        assert t2 not in telefonemas_c1
        assert t2 not in telefonemas_c2
        assert t3 in telefonemas_c1
        assert t3 not in telefonemas_c2
        assert t4 in telefonemas_c2
        assert t4 not in telefonemas_c1
        assert t5 not in telefonemas_c1
        assert t5 not in telefonemas_c2
    
    
    def set_moradores(self):
        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 3, 6),
            logradouro = 'R. dos Bobos, nº 0')
            
        p1 = Pessoa(nome = 'André')
        p2 = Pessoa(nome = 'Marcos')
        
        m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 3, 6))
        m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 3, 6))
        self.moradores = [m1, m2]
        
        td1 = TipoDespesa(nome = 'Água',     republica = r)
        td2 = TipoDespesa(nome = 'Aluguel',  republica = r)
        td3 = TipoDespesa(nome = 'Internet', republica = r)
        self.tipos_despesa = [td1, td2, td3]
        
        Session.commit()
        
    
    def set_despesas(self):
        self.set_moradores()
        td1, td2, td3 = self.tipos_despesa
        m1, m2        = self.moradores
    
        d1 = Despesa(data = date(2007, 4, 10), quantia = 20, tipo = td1, responsavel = m1)
        d2 = Despesa(data = date(2007, 4, 21), quantia = 50, tipo = td2, responsavel = m1)
        d3 = Despesa(data = date(2007, 4, 21), quantia = 50, tipo = td2, responsavel = m2)
        self.despesas = [d1, d2, d3]
        
        Session.commit()
    
    
    def test_despesas(self):
        self.set_despesas()
        
        m1         = self.moradores[0]
        d1, d2, d3 = self.despesas      
        
        despesas = m1.despesas(date(2007, 4, 10), date(2007, 5, 10))
        
        assert d1 in despesas
        assert d2 in despesas
        assert d3 not in despesas
    
    
    def set_despesas_periodicas(self):
        self.set_moradores()
        td1, td2, td3 = self.tipos_despesa
        m1, m2        = self.moradores
    
        dp1 = DespesaPeriodica(
                quantia            = 50,
                tipo               = td3,
                responsavel        = m1,
                proximo_vencimento = date(2007, 4, 19),
                data_termino       = date(2007, 7, 10)
                )
        dp2 = DespesaPeriodica(quantia = 45, tipo = td1, responsavel = m1, proximo_vencimento = date(2007, 5, 2))
        dp3 = DespesaPeriodica(quantia = 10, tipo = td2, responsavel = m1, proximo_vencimento = date(2007, 6, 1))
        
        self.despesas = [dp1, dp2, dp3]
        
        Session.commit()
        
    def test_despesa_periodica_1(self):
        self.set_despesas_periodicas()
        m1 = self.moradores[0]
        dp1, dp2, dp3 = self.despesas
        
        despesas = m1.despesas(date(2007, 4, 10), date(2007, 5, 10))
        
        d1 = Despesa.get_by(data = date(2007, 4, 19))
        d2 = Despesa.get_by(data = date(2007, 5, 2))
        d3 = Despesa.get_by(data = date(2007, 6, 1))
        
        assert d1 in despesas
        assert d2 in despesas
        assert d3 is None
        assert dp1.proximo_vencimento == date(2007, 5, 19)
        assert dp2.proximo_vencimento == date(2007, 6, 2)
        assert dp3.proximo_vencimento == date(2007, 6, 1)
        
    
    def test_despesa_periodica_2(self):
        self.set_despesas_periodicas()
        m1 = self.moradores[0]
        dp1, dp2, dp3 = self.despesas
        
        despesas = set(m1.despesas(date(2007, 4, 10), date(2007, 8, 10)))
        
        d1 = set(Despesa.query.filter(Despesa.data.between(date(2007, 4, 10), date(2007, 5, 9))))
        d2 = set(Despesa.query.filter(Despesa.data.between(date(2007, 5, 10), date(2007, 6, 9))))
        d3 = set(Despesa.query.filter(Despesa.data.between(date(2007, 6, 10), date(2007, 7, 9))))
        d4 = set(Despesa.query.filter(Despesa.data.between(date(2007, 7, 10), date(2007, 8, 10))))
        
        assert len(d1) == 2
        assert len(d2) == 3
        assert len(d3) == 3
        assert len(d4) == 2
        assert d1.issubset(despesas)
        assert d2.issubset(despesas)
        assert d3.issubset(despesas)
        assert d4.issubset(despesas)
        
        
    def test_peso_quota(self):
        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 3, 6),
            logradouro = 'R. dos Bobos, nº 0')
            
        p1 = Pessoa(nome = 'André')
        p2 = Pessoa(nome = 'Marcos')
        p3 = Pessoa(nome = 'Roger')
        p4 = Pessoa(nome = 'Leonardo')
        m1 = Morador(pessoa = p1, republica = r, data_entrada = date(2007, 1, 1))
        m2 = Morador(pessoa = p2, republica = r, data_entrada = date(2007, 1, 2))
        m3 = Morador(pessoa = p3, republica = r, data_entrada = date(2007, 1, 3))
        m4 = Morador(pessoa = p4, republica = r, data_entrada = date(2007, 1, 4))
        
        PesoQuota(morador = m1, peso_quota = Decimal(22), data_cadastro = date(2007, 3, 6))
        PesoQuota(morador = m1, peso_quota = Decimal(20), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = m1, peso_quota = Decimal(15), data_cadastro = date(2007, 5, 6))
        
        Session.commit()
        Session.expunge_all()
        
        m1 = Morador.get_by(data_entrada = date(2007, 1, 1))
        
        assert m1.peso_quota(date(2007, 2, 1)) == 25
        assert m1.peso_quota(date(2007, 3, 6)) == m1.peso_quota(date(2007, 4, 5)) == 22
        assert m1.peso_quota(date(2007, 4, 6)) == m1.peso_quota(date(2007, 5, 5)) == 20
        assert m1.peso_quota(date(2007, 5, 6)) == m1.peso_quota(date(2007, 6, 6)) == 15