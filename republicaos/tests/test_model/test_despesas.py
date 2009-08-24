#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from datetime   import date, time
from decimal    import Decimal
from dateutil.relativedelta import relativedelta
from republicaos.model import Republica, Fechamento, ContaTelefone, Pessoa, Morador, Telefonema, TelefoneRegistrado
from republicaos.model import TipoDespesa, DespesaAgendada, Despesa
from republicaos.tests import Session, TestModel

class TestMorador(TestModel):

    # desabilitado
    def _test_telefonemas(self):
        p1 = Pessoa(nome = 'André', senha = '1234', email = 'xyz@xyz.com')

        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 3, 6),
            logradouro = 'R. dos Bobos, n 0',
            cidade = 'AbC',
            uf = 'ES')

        Morador(pessoa = p1, republica = r, entrada = date(2007, 3, 6), saida = date(2006, 12, 1))

        TelefoneRegistrado(numero = 1234, descricao = 'tel. do trabalho', republica = r, responsavel = p1)
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
        self.r = Republica(nome = 'Teste',
            data_criacao = date(2007, 3, 6),
            logradouro = 'R. dos Bobos, n. 0',
            cidade = 'ABC',
            uf = 'AA')


        p1 = Pessoa(nome = 'André', senha = '1234', email = 'xyz@xyz.com')
        p2 = Pessoa(nome = 'Marcos', senha = '1234', email = 'yzx@xyz.com')
        self.pessoas = [p1, p2]

        Morador(pessoa = p1, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = p2, republica = self.r, entrada = date(2007, 3, 6))

        td1 = TipoDespesa(nome = 'Água',     republica = self.r)
        td2 = TipoDespesa(nome = 'Aluguel',  republica = self.r)
        td3 = TipoDespesa(nome = 'Internet', republica = self.r)
        self.tipos_despesa = [td1, td2, td3]

        Session.commit()


    def set_despesas(self):
        self.set_moradores()
        td1, td2, td3 = self.tipos_despesa
        p1, p2        = self.pessoas

        d1 = Despesa(lancamento = date(2007, 4, 10), quantia = 20, tipo = td1, pessoa = p1, republica = self.r)
        d2 = Despesa(lancamento = date(2007, 4, 21), quantia = 50, tipo = td2, pessoa = p1, republica = self.r)
        d3 = Despesa(lancamento = date(2007, 4, 21), quantia = 50, tipo = td2, pessoa = p2, republica = self.r)
        self.despesas = [d1, d2, d3]

        Session.commit()


    def test_despesas(self):
        self.set_despesas()

        p1         = self.pessoas[0]
        d1, d2, d3 = self.despesas

        despesas = Despesa.get_despesas_no_periodo(pessoa = p1, data_inicial=date(2007, 4, 10), data_final=date(2007, 5, 10))

        assert d1 in despesas
        assert d2 in despesas
        assert d3 not in despesas


    def set_despesas_periodicas(self):
        self.set_moradores()
        td1, td2, td3 = self.tipos_despesa
        p1, p2        = self.pessoas

        dp1 = DespesaAgendada(
                quantia            = 50,
                tipo               = td3,
                pessoa        = p1,
                proximo_lancamento = date(2007, 4, 19),
                termino       = date(2007, 7, 10),
                republica          = self.r
                )
        dp2 = DespesaAgendada(quantia = 45, tipo = td1, pessoa = p1, proximo_lancamento = date(2007, 5, 2), republica = self.r)
        dp3 = DespesaAgendada(quantia = 10, tipo = td2, pessoa = p1, proximo_lancamento = date(2007, 6, 10), republica = self.r)

        self.despesas_agendadas = [dp1, dp2, dp3]

        Session.commit()

    def test_despesa_periodica(self):
        self.set_despesas_periodicas()
        td1, td2, td3 = self.tipos_despesa
        p1 = self.pessoas[0]

        despesas = Despesa.get_despesas_no_periodo(data_inicial = date(2007, 4, 10), data_final = date(2007, 5, 10), pessoa = p1)
        d1 = Despesa.get_by(tipo = td3, lancamento = date(2007, 4, 19))
        d2 = Despesa.get_by(tipo = td1, lancamento = date(2007, 5, 2))

        assert d1 in despesas
        assert d2 in despesas

        hoje = date.today()
        mes_q_vem = hoje + relativedelta(months=1)
        mes_passado = hoje - relativedelta(months=1)

        assert Despesa.get_by(lancamento = date(mes_passado.year, mes_passado.month, 2)) is not None
        assert Despesa.get_by(lancamento = date(mes_passado.year, mes_passado.month, 10)) is not None

        dp1, dp2, dp3 = self.despesas_agendadas

        assert dp1 not in Session # foi deletado pois o prazo chegou ao fim
        assert hoje < dp2.proximo_lancamento <= date(mes_q_vem.year, mes_q_vem.month, 2), dp2.proximo_lancamento
        assert hoje < dp3.proximo_lancamento <= date(mes_q_vem.year, mes_q_vem.month, 10), dp3.proximo_lancamento


    # desabilitado
    def _test_peso_quota(self):
        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 3, 6),
            logradouro = 'R. dos Bobos, n. 0',
            cidade = 'ABC',
            uf = 'AA')

        p1 = Pessoa(nome = 'André', senha = '1234', email = 'xyz@xyz.com')
        p2 = Pessoa(nome = 'Marcos', senha = '1234', email = 'yzx@xyz.com')
        p3 = Pessoa(nome = 'Roger', senha = '1234', email = 'zyx@xyz.com')
        p4 = Pessoa(nome = 'Leonardo', senha = '1234', email = 'ijk@xyz.com')

        m1 = Morador(pessoa = p1, republica = r, entrada = date(2007, 1, 1))
        m2 = Morador(pessoa = p2, republica = r, entrada = date(2007, 1, 2))
        m3 = Morador(pessoa = p3, republica = r, entrada = date(2007, 1, 3))
        m4 = Morador(pessoa = p4, republica = r, entrada = date(2007, 1, 4))

        PesoQuota(morador = m1, peso_quota = Decimal(22), data_cadastro = date(2007, 3, 6))
        PesoQuota(morador = m1, peso_quota = Decimal(20), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = m1, peso_quota = Decimal(15), data_cadastro = date(2007, 5, 6))

        Session.commit()
        Session.expunge_all()

        m1 = Morador.get_by(entrada = date(2007, 1, 1))

        assert m1.peso_quota(date(2007, 2, 1)) == 25
        assert m1.peso_quota(date(2007, 3, 6)) == m1.peso_quota(date(2007, 4, 5)) == 22
        assert m1.peso_quota(date(2007, 4, 6)) == m1.peso_quota(date(2007, 5, 5)) == 20
        assert m1.peso_quota(date(2007, 5, 6)) == m1.peso_quota(date(2007, 6, 6)) == 15
