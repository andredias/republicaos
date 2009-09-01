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

    def test_despesas(self):
        mes_passado = date.today() - relativedelta(months=1)
        hoje = date.today()
        r = Republica(nome = 'Teste',
            data_criacao = mes_passado,
            logradouro = 'R. dos Bobos, n. 0',
            cidade = 'ABC',
            uf = 'AA')
        Fechamento(data=date.today(), republica=r)
        Fechamento(data=date.today() + relativedelta(months=1), republica=r)

        p1 = Pessoa(nome = 'André', senha = '1234', email = 'xyz@xyz.com')
        p2 = Pessoa(nome = 'Marcos', senha = '1234', email = 'yzx@xyz.com')

        Morador(pessoa = p1, republica = r, entrada = mes_passado)
        Morador(pessoa = p2, republica = r, entrada = mes_passado)

        Session.commit()
        td1, td2, td3 = r.tipos_despesa[0:3]
        inicio, fim = r.fechamento_atual.intervalo
        d1 = Despesa(lancamento=inicio, quantia = 20, tipo = td1, pessoa = p1, republica = r)
        d2 = Despesa(lancamento=fim, quantia = 50, tipo = td2, pessoa = p1, republica = r)
        d3 = Despesa(lancamento=inicio - relativedelta(days=1), quantia=50, tipo=td2, pessoa=p2, republica = r)

        despesas = Despesa.get_despesas_no_periodo(pessoa = p1, data_inicial=inicio, data_final=fim)

        assert d1 in despesas
        assert d2 in despesas
        assert d3 not in despesas

        dp1 = DespesaAgendada(
                    quantia = 50,
                    tipo = td3,
                    pessoa = p1,
                    proximo_lancamento = hoje,
                    termino = hoje,
                    republica = r
                    )
        dp2 = DespesaAgendada(
                    quantia = 45,
                    tipo = td1,
                    pessoa = p1,
                    proximo_lancamento = fim - relativedelta(months=1),
                    republica = r
                    )
        dp3 = DespesaAgendada(
                    quantia = 10,
                    tipo = td2,
                    pessoa = p1,
                    proximo_lancamento = hoje + relativedelta(months=1),
                    republica =r
                    )
        Session.commit()
        despesas = Despesa.get_despesas_no_periodo(
                                data_inicial = inicio,
                                data_final = fim,
                                pessoa = p1
                                )
        d1 = Despesa.get_by(tipo = td3, lancamento = hoje, republica = r)

        assert d1 != None and d1 in despesas
        assert len(despesas) == 3
        assert dp1 not in Session # foi deletado pois o prazo chegou ao fim

