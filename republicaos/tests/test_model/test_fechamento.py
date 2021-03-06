#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from datetime   import date, time
from decimal    import Decimal
from dateutil.relativedelta import relativedelta
from republicaos.model import Republica, Fechamento, ContaTelefone, Pessoa, Morador, Telefonema, TelefoneRegistrado
from republicaos.model import TipoDespesa, DespesaAgendada, Despesa
from republicaos.tests import Session, TestModel
from exibicao_resultados import print_acerto_final, print_calculo_quotas_participantes, print_rateio_conta_telefone, print_fechamento
from republicaos.lib.utils import float_equal


class TestFechamento(TestModel):
    '''
    Testa o fechamento das contas do mês
    '''
    #url = 'postgres://turbo_gears:tgears@localhost/tg_teste'

    def setUp(self):
        TestModel.setUp(self)

        self.r = Republica(nome = 'Teste',
            data_criacao = date(2007, 1, 1),
            endereco = 'R. dos Bobos, n. 0, Sumare, SP',
            latitude = 0,
            longitude = 0)
        Fechamento(data = date(2007, 4, 6), republica = self.r)
        Fechamento(data = date.today() + relativedelta(days=1), republica = self.r)
        Fechamento(data = date.today() + relativedelta(months=1), republica = self.r)

        self.p1 = Pessoa(nome = 'André', senha = '1234', email = 'xyz@xyz.com')
        self.p2 = Pessoa(nome = 'Marcos', senha = '1234', email = 'yzx@xyz.com')
        self.p3 = Pessoa(nome = 'Roger', senha = '1234', email = 'zyx@xyz.com')
        self.p4 = Pessoa(nome = 'Leonardo', senha = '1234', email = 'ijk@xyz.com')


        self.c = ContaTelefone(
                telefone = 2409,
                operadora_id = 1,
                emissao = date(2007, 4, 29),
                vencimento = date(2007, 5, 2),
                franquia = Decimal(30),
                servicos = Decimal(0),
                republica = self.r
            )

        TipoDespesa(nome = 'Internet', republica = self.r)
        TipoDespesa(nome = 'Telefone', republica = self.r)

        Session.commit()
        self.td1, self.td2, self.td3, self.td4, self.td5 = self.r.tipos_despesa[0:5]




    def test_acerto_final_1(self):
        '''
        Acerto Final - Caso 1: 2 credores e 2 devedores
        '''
        f = Fechamento(data = date(2007, 5, 6), republica = self.r)
        m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 3, 6))
        m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 3, 6))
        m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 3, 6))
        m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6))

        Despesa(lancamento = date(2007, 4, 21), quantia = 225, tipo = self.td1, pessoa = self.p1, republica = self.r)
        Despesa(lancamento = date(2007, 4, 12), quantia = 75, tipo = self.td3, pessoa = self.p2, republica = self.r)
        Despesa(lancamento = date(2007, 5, 1), quantia = 200, tipo = self.td2, pessoa = self.p3, republica = self.r)

        Session.commit()

        f.executar_rateio()
        print_acerto_final(f)

        assert f.saldo_final[self.p1] == -100
        assert f.saldo_final[self.p2] == 50
        assert f.saldo_final[self.p3] == -75
        assert f.saldo_final[self.p4] == 125

        assert self.p1 not in f.acerto_a_pagar
        assert self.p3 not in f.acerto_a_pagar
        assert self.p2 in f.acerto_a_pagar
        assert self.p4 in f.acerto_a_pagar
        assert sum(quantia for quantia in f.acerto_a_pagar[self.p2].values()) == Decimal(50)
        assert sum(quantia for quantia in f.acerto_a_pagar[self.p4].values()) == Decimal(125)
        assert sum(quantia for quantia in f.acerto_a_receber[self.p1].values()) == Decimal(100)
        assert sum(quantia for quantia in f.acerto_a_receber[self.p3].values()) == Decimal(75)
        assert sum(f.saldo_final[pessoa] for pessoa in f.participantes) == 0



    def test_acerto_final_2(self):
        '''
        Acerto Final - Caso 2: 1 credor e 3 devedores
        '''
        f = Fechamento(data = date(2007, 5, 6), republica=self.r)

        m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 3, 6))
        m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 3, 6))
        m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 3, 6))
        m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6))

        Despesa(lancamento = date(2007, 4, 12), quantia = 75, tipo = self.td3, pessoa = self.p2, republica = self.r)
        Despesa(lancamento = date(2007, 5, 1), quantia = 100, tipo = self.td2, pessoa = self.p3, republica = self.r)
        Despesa(lancamento = date(2007, 4, 21), quantia = 325, tipo = self.td1, pessoa = self.p4, republica = self.r)

        Session.commit()

        f.executar_rateio()
        print_acerto_final(f)

        assert f.saldo_final[self.p1] == 125
        assert f.saldo_final[self.p2] == 50
        assert f.saldo_final[self.p3] == 25
        assert f.saldo_final[self.p4] == -200

        assert self.p1 in f.acerto_a_pagar and self.p2 in f.acerto_a_pagar and self.p3 in f.acerto_a_pagar
        assert self.p4 not in f.acerto_a_pagar and self.p4 in f.acerto_a_receber
        assert sum(quantia for quantia in f.acerto_a_pagar[self.p1].values()) == 125
        assert sum(quantia for quantia in f.acerto_a_pagar[self.p2].values()) == 50
        assert sum(quantia for quantia in f.acerto_a_pagar[self.p3].values()) == 25
        assert sum(quantia for quantia in f.acerto_a_receber[self.p4].values()) == 200
        assert len(f.acerto_a_pagar[self.p1]) == len(f.acerto_a_pagar[self.p2]) == len(f.acerto_a_pagar[self.p3]) == 1
        assert sum(f.saldo_final[pessoa] for pessoa in f.participantes) == 0



    def test_acerto_final_3(self):
        '''
        Acerto Final - Caso 3: 3 credores e 1 devedor
        '''
        f = Fechamento(data = date(2007, 5, 6), republica=self.r)

        Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6))

        Despesa(lancamento = date(2007, 4, 12), quantia = 175, tipo = self.td3, pessoa = self.p1, republica = self.r)
        Despesa(lancamento = date(2007, 4, 12), quantia = 50, tipo = self.td3, pessoa = self.p2, republica = self.r)
        Despesa(lancamento = date(2007, 5, 1), quantia = 200, tipo = self.td2, pessoa = self.p3, republica = self.r)
        Despesa(lancamento = date(2007, 4, 21), quantia = 175, tipo = self.td1, pessoa = self.p4, republica = self.r)

        Session.commit()

        f.executar_rateio()
        print_acerto_final(f)

        assert f.saldo_final[self.p1] == -25
        assert f.saldo_final[self.p2] == 100
        assert f.saldo_final[self.p3] == -50
        assert f.saldo_final[self.p4] == -25

        assert self.p1 not in f.acerto_a_pagar and self.p3 not in f.acerto_a_pagar and self.p4 not in f.acerto_a_pagar
        assert sum(quantia for quantia in f.acerto_a_receber[self.p1].values()) == 25
        assert sum(quantia for quantia in f.acerto_a_receber[self.p3].values()) == 50
        assert sum(quantia for quantia in f.acerto_a_receber[self.p4].values()) == 25
        assert sum(quantia for quantia in f.acerto_a_pagar[self.p2].values()) == 100
        assert sum(f.saldo_final[pessoa] for pessoa in f.participantes) == 0


    def test_acerto_final_4(self):
        '''
        Acerto Final - Caso 4: 0 credores e 0 devedores
        '''
        f = Fechamento(data = date(2007, 5, 6), republica=self.r)

        Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 3, 6))
        Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6))

        Despesa(lancamento = date(2007, 4, 12), quantia = 50, tipo = self.td3, pessoa = self.p1, republica = self.r)
        Despesa(lancamento = date(2007, 4, 12), quantia = 50, tipo = self.td3, pessoa = self.p2, republica = self.r)
        Despesa(lancamento = date(2007, 5, 1), quantia = 50, tipo = self.td2, pessoa = self.p3, republica = self.r)
        Despesa(lancamento = date(2007, 4, 21), quantia = 50, tipo = self.td1, pessoa = self.p4, republica = self.r)

        f.executar_rateio()
        print_acerto_final(f)

        assert len(f.acerto_a_pagar) == 0
        assert sum(f.saldo_final[p] for p in (self.p1, self.p2, self.p3, self.p4)) == 0


    def assert_geral_fechamento(self, fechamento):
        assert fechamento.total_despesas > 0
        assert any(fechamento.saldo_final[participante] for participante in fechamento.participantes)
        assert float_equal(fechamento.total_despesas, sum(fechamento.rateio(morador) for morador in fechamento.participantes) + fechamento.total_telefone())
        assert float_equal(sum(fechamento.saldo_final(participante) for participante in fechamento.participantes), 0.0)
        for credor, creditos in fechamento.acerto_a_receber.items():
            assert sum(creditos.values()) == abs(fechamento.saldo_final(credor))
        for devedor, dividas in fechamento.acerto_a_pagar.items():
            assert sum(dividas.values()) == abs(fechamento.saldo_final(devedor))



    # desabilitado
    def _test_fechamento_1(self):
        from test_dividir_conta_telefone import TestDividirContaTelefone
        from exibicao_resultados         import print_rateio_conta_telefone, print_fechamento
        # utiliza o test_dividir_conta_telefone
        testa_conta = TestDividirContaTelefone()
        testa_conta.r = self.r
        testa_conta.c = self.c
        testa_conta.p1 = self.p1
        testa_conta.p2 = self.p2
        testa_conta.p3 = self.p3
        testa_conta.p4 = self.p4
        testa_conta.p5 = self.p5 = Pessoa(nome = 'Alexandre')
        self.p5.commit()

        f = Fechamento(data = date(2007, 5, 6), republica=self.r)

        testa_conta.test_dividir_conta_caso_15()

        self.m1 = testa_conta.m1
        self.m2 = testa_conta.m2
        self.m3 = testa_conta.m3
        self.m4 = testa_conta.m4

        Despesa(lancamento = date(2007, 4, 21), quantia = 20, tipo = self.td1, pessoa = self.m1, republica = self.r)
        Despesa(lancamento = date(2007, 4, 12), quantia = 50, tipo = self.td3, pessoa = self.m2, republica = self.r)
        Despesa(lancamento = date(2007, 4, 21), quantia = 150, tipo = self.td2, pessoa = self.m2, republica = self.r)
        Despesa(lancamento = date(2007, 5, 1), quantia = 150, tipo = self.td2, pessoa = self.m3, republica = self.r)
        Despesa(lancamento = date(2007, 5, 5), quantia = self.c.total, tipo = self.td5, pessoa = self.m1, republica = self.r)

        DespesaAgendada(quantia = 50, tipo = self.td4, pessoa = self.m1, proximo_lancamento = date(2007, 4, 19), republica = self.r)
        DespesaAgendada(quantia = 45, tipo = self.td1, pessoa = self.m1, proximo_lancamento = date(2007, 6, 1), republica = self.r)

        Session.commit()

        print_fechamento(f)

        assert len(f.participantes) == 5
        self.assert_geral_fechamento(f)


    # Desabilitado
    def _test_fechamento_2(self):
        '''
        Fechamento sem nenhum ex-morador
        '''
        from test_dividir_conta_telefone import TestDividirContaTelefone
        from exibicao_resultados         import print_rateio_conta_telefone, print_fechamento
        # utiliza o test_dividir_conta_telefone
        testa_conta = TestDividirContaTelefone()
        testa_conta.r = self.r
        testa_conta.c = self.c
        testa_conta.p1 = self.p1
        testa_conta.p2 = self.p2
        testa_conta.p3 = self.p3

        f = Fechamento(data=self.r.proximo_fechamento, republica=self.r)

        testa_conta.test_dividir_conta_caso_07()

        self.m1 = testa_conta.m1
        self.m2 = testa_conta.m2
        self.m3 = testa_conta.m3

        Despesa(lancamento = date(2007, 4, 21), quantia = Decimal(20), tipo = self.td1, pessoa = self.m1, republica = self.r)
        Despesa(lancamento = date(2007, 4, 12), quantia = Decimal(50), tipo = self.td3, pessoa = self.m2, republica = self.r)
        Despesa(lancamento = date(2007, 4, 21), quantia = Decimal(150), tipo = self.td2, pessoa = self.m2, republica = self.r)
        Despesa(lancamento = date(2007, 5, 1), quantia = Decimal(150), tipo = self.td2, pessoa = self.m3, republica = self.r)
        Despesa(lancamento = date(2007, 5, 5), quantia = (self.c.total / Decimal(2)), tipo = self.td5, pessoa = self.m1, republica = self.r)
        Despesa(lancamento = date(2007, 5, 5), quantia = (self.c.total / Decimal(2)), tipo = self.td5, pessoa = self.m2, republica = self.r)

        DespesaAgendada(quantia = 150, tipo = self.td4, pessoa = self.m1, proximo_lancamento = date(2007, 4, 19), republica = self.r)
        DespesaAgendada(quantia = 45, tipo = self.td1, pessoa = self.m1, proximo_lancamento = date(2007, 6, 1), republica = self.r)

        Session.commit()

        print_fechamento(f)

        assert f.total_telefone() == self.c.total
        assert len(f.participantes) == 3
        self.assert_geral_fechamento(f)


    def test_fechamento_3(self):
        '''
        Fechamento sem nenhum morador
        '''
        f = Fechamento(data = date(2007, 5, 6), republica=self.r)
        f.executar_rateio()
        print_fechamento(f)

        assert f.total_despesas == 0
        assert len(f.participantes) == 0
        assert sum(f.saldo_final(participante) for participante in f.participantes) == 0


    def _test_calculo_quotas_participantes_1(self):
        '''
        Teste do cálculo da proporção de cada morador. Único intervalo e sem porcentagem cadastrada
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 3, 6), saida = date(2007, 5, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 3, 6), saida = date(2007, 5, 6))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 3, 6), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6), saida = date(2007, 5, 6))

        f = Fechamento(date(2007, 5, 6), republica=self.r)
        f.executar_rateio()
        Session.commit()

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 1
        assert f.intervalos[0].data_inicial == date(2007, 4, 6)
        assert f.intervalos[0].data_final == date(2007, 5, 6)
        assert len(f.participantes) == 4
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)

        for morador in f.participantes:
            assert f.quota(morador) == f.quota_peso(morador) == 25


    def _test_calculo_quotas_participantes_2(self):
        '''
        Teste do cálculo da proporção de cada morador. Sem porcentagem cadastrada. Um morador sai em um dia e outro entra no dia seguinte
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 20))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 21), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6), saida = date(2007, 5, 6))
        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 2
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 21)
        assert f.intervalos[1].data_inicial == date(2007, 4, 21) and f.intervalos[1].data_final == date(2007, 5, 6)
        assert len(f.intervalos[0].participantes) == len(f.intervalos[1].participantes) == 3
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
        assert float_equal(f.quota(self.m1), 33.333)
        assert float_equal(f.quota(self.m2), 16.667)
        for morador in f.participantes:
            assert float_equal(f.quota(morador), f.quota_peso(morador))


    def _test_calculo_quotas_participantes_3(self):
        '''
        Teste do cálculo da proporção de cada morador. Períodos iguais e sem porcentagem cadastrada
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 20))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 20), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 3, 6), saida = date(2007, 5, 6))
        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 3
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 20)
        assert f.intervalos[1].data_inicial == date(2007, 4, 20) and f.intervalos[1].data_final == date(2007, 4, 21)
        assert f.intervalos[2].data_inicial == date(2007, 4, 21) and f.intervalos[2].data_final == date(2007, 5, 6)
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
        assert float_equal(f.intervalos[1].quota(self.m1), 0.833)
        assert float_equal(f.intervalos[2].quota(self.m1), 16.667)
        for morador in f.participantes:
            assert float_equal(f.quota(morador), f.quota_peso(morador))


    def _test_calculo_quotas_participantes_4(self):
        '''
        Teste do cálculo da proporção de cada morador. Um intervalo sem ninguém e sem porcentagem cadastrada
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 20))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 20))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 25), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 4, 30), saida = date(2007, 5, 6))
        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 4
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 21)
        assert f.intervalos[1].data_inicial == date(2007, 4, 21) and f.intervalos[1].data_final == date(2007, 4, 25)
        assert f.intervalos[2].data_inicial == date(2007, 4, 25) and f.intervalos[2].data_final == date(2007, 4, 30)
        assert f.intervalos[3].data_inicial == date(2007, 4, 30) and f.intervalos[3].data_final == date(2007, 5, 6)
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
        assert f.total_dias == 26
        for morador in f.participantes:
            assert float_equal(f.quota(morador), f.quota_peso(morador))


    def _test_calculo_quotas_participantes_5(self):
        '''
        Teste do cálculo da proporção de cada morador. Datas ajustadas para dar 1/5 para um e 2/5 para os outros dois moradores
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 3, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 3, 6))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 18))
        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 2
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 18)
        assert f.intervalos[1].data_inicial == date(2007, 4, 18) and f.intervalos[1].data_final == date(2007, 5, 6)
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
        for morador in f.participantes:
            assert float_equal(f.quota(morador), f.quota_peso(morador))


    def _test_calculo_quotas_participantes_peso_1(self):
        '''
        Teste do cálculo da proporção de cada morador. Um intervalo único e COM porcentagem cadastrada dando 100%
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))

        PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m2, peso_quota = Decimal(25), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m3, peso_quota = Decimal(15), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))

        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 1
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 5, 6)
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
        assert f.total_dias == 30
        for participante in f.participantes:
            assert f.quota(participante) == 25
            assert float_equal(participante.peso_quota(f.data_inicial), f.quota_peso(participante))


    def _test_calculo_quotas_participantes_peso_2(self):
        '''
        Teste do cálculo da proporção de cada morador. Três intervalos e COM porcentagem cadastrada
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 15))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 4, 21), saida = date(2007, 5, 6))

        PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m2, peso_quota = Decimal(25), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m3, peso_quota = Decimal(15), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))

        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 3
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 16)
        assert f.intervalos[1].data_inicial == date(2007, 4, 16) and f.intervalos[1].data_final == date(2007, 4, 21)
        assert f.intervalos[2].data_inicial == date(2007, 4, 21) and f.intervalos[2].data_final == date(2007, 5, 6)
        assert f.intervalos[2].quota_peso(self.m1) == f.intervalos[2].quota_peso(self.m4) == 2 * f.intervalos[2].quota_peso(self.m3)
        assert float_equal(f.quota_peso(self.m1), 2 * f.quota_peso(self.m3))
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)


    def _test_calculo_quotas_participantes_peso_3(self):
        '''
        Teste do cálculo da proporção de cada morador. Porcentagem maior que 100%
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 5, 6))

        PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m2, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m3, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))

        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 1
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 5, 6)
        assert f.quota_peso(self.m1) == f.quota_peso(self.m4) == 20
        assert f.quota_peso(self.m2) == f.quota_peso(self.m3) == 30
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)


    def _test_calculo_quotas_participantes_peso_4(self):
        '''
        Teste do cálculo da proporção de cada morador. Um intervalo sem ninguém. Porcentagem maior que 100%
        '''
        self.m1 = Morador(pessoa = self.p1, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 20))
        self.m2 = Morador(pessoa = self.p2, republica = self.r, entrada = date(2007, 4, 6), saida = date(2007, 4, 20))
        self.m3 = Morador(pessoa = self.p3, republica = self.r, entrada = date(2007, 4, 25), saida = date(2007, 5, 6))
        self.m4 = Morador(pessoa = self.p4, republica = self.r, entrada = date(2007, 4, 30), saida = date(2007, 5, 6))

        PesoQuota(morador = self.m1, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m2, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m3, peso_quota = Decimal(45), data_cadastro = date(2007, 4, 6))
        PesoQuota(morador = self.m4, peso_quota = Decimal(30), data_cadastro = date(2007, 4, 6))

        Session.commit()

        f = Fechamento(date(2007, 5, 6), republica=self.r)

        print_calculo_quotas_participantes(f)

        assert len(f.intervalos) == 4
        assert f.intervalos[0].data_inicial == date(2007, 4, 6) and f.intervalos[0].data_final == date(2007, 4, 21)
        assert f.intervalos[1].data_inicial == date(2007, 4, 21) and f.intervalos[1].data_final == date(2007, 4, 25)
        assert f.intervalos[2].data_inicial == date(2007, 4, 25) and f.intervalos[2].data_final == date(2007, 4, 30)
        assert f.intervalos[3].data_inicial == date(2007, 4, 30) and f.intervalos[3].data_final == date(2007, 5, 6)
        assert float_equal(sum(f.quota(morador) for morador in f.participantes), 100.0)
        assert float_equal(sum(f.quota_peso(morador) for morador in f.participantes), 100.0)
        assert f.total_dias == 26
    
    def test_fechamento_atual(self):
        assert self.r.fechamento_atual.data == date.today() + relativedelta(days=1)
