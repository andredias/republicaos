#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from datetime   import date, time
from decimal    import Decimal
from dateutil.relativedelta import relativedelta
from republicaos.model import Republica, Fechamento, ContaTelefone, Pessoa, Morador, Telefonema, TelefoneRegistrado, TipoDespesa
from republicaos.model import TipoDespesa, DespesaAgendada, Despesa
from republicaos.tests import Session, TestModel


class TestRepublica(TestModel):

    def test_fechamento(self):
        mes_retrasado = date.today() - relativedelta(months=2)
        mes_q_vem = date.today() + relativedelta(months=1)
        r = Republica(nome = 'Teste',
            data_criacao = mes_retrasado,
            endereco = 'R. dos Bobos, n. 0, Sumare, SP',
            latitude = 0,
            longitude = 0)
        Fechamento(data=date.today(), republica=r)
        Fechamento(data=mes_q_vem, republica=r)
        Fechamento(data=date.today() + relativedelta(months=2), republica=r)
        Session.commit()
        
        inicio, fim = r.fechamento_atual.intervalo
        
        assert inicio == mes_retrasado
        assert r.fechamento_atual.data == date.today()
        assert len(r.fechamentos) == 3

        Session.expunge_all()
        
#        r = Republica.get_by()
#        r._preencher_fechamentos()
#        assert len(r.tipos_despesa) > 0
#        assert len(r.fechamentos) == 3, r.fechamentos
#        assert r.fechamento_atual.data == date.today() + relativedelta(months=1)
        
        
        # verificar _check_proximo_fechamento
        r2 = Republica(nome = 'Mae Joana',
            endereco = 'R. tralala, Vitoria, ES',
            latitude = 0,
            longitude = 0)
        Session.commit()
        
        assert r2.data_criacao == r2.fechamento_atual.intervalo[0] == date.today()
        assert r2.fechamento_atual.data == date.today() + relativedelta(months=1)
    
    
    def test_fechamento_atual(self):
        r = Republica(nome = 'Teste',
            data_criacao = date.today() - relativedelta(months=2),
            endereco = 'R. dos Bobos, n. 0, Sumare, SP',
            latitude = 0,
            longitude = 0)
        Fechamento(data=date.today() - relativedelta(months=1), republica=r)
        f = Fechamento(data=date.today(), republica=r)
        Fechamento(data=date.today() + relativedelta(months=1), republica=r)
        Session.commit()
        
        assert r.fechamento_atual == f


    def test_moradores(self):
        '''
        Testa quais moradores entram ou n??o em um determinado per??odo de fechamento.

        Escrito de outras formas, o per??odo de apura????o pode ser definido como:
           * `[dia/m??s, dia/(m??s+1)[`
           * `----[xxxxxx[`--->`

        Casos de apura????o:

                                Per??odo de Apura????o
        -------------------[xxxxxxxxxxxxxxxxxxxxxxxxxxxxx]------------------>    Morador     |  Inclu??do
                           |                             |
        -------[yyyyyyyyyyyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxzzzzzzzzzzzzzzzz-->    Morador_1   |  X
                           |                             |
        ------------------------[xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-->    Morador_2   |  X
                           |                             |
        -------[yyyyyyyyyyyxxxxxxxxxxxxxxx]--------------------------------->    Morador_3   |  X
                           |                             |
        --------------------------[xxxxxxxxx]------------------------------->    Morador_4   |  X
                           |                             |
        --------------------------------------------------------[zzzzzzzzz-->    Morador_5   |
                           |                             |
        -------------------------------------------------[zzzzzzzz]--------->    Morador_6   |  X
                           |                             |
        -------[yyyyyyyy]--------------------------------------------------->    Morador_7   |
                           |                             |
        ---------[yyyyyyyyy]------------------------------------------------>    Morador_8   |  X
        '''
        r = Republica(nome = 'Teste',
            data_criacao = date(2007, 4, 8),
            endereco = 'R. dos Bobos, n. 0, Sumare, SP',
            latitude = 0,
            longitude = 0)

        p1 = Pessoa(nome = '1', senha='1234', email='1@xyz.com')
        p2 = Pessoa(nome = '2', senha='1234', email='2@xyz.com')
        p3 = Pessoa(nome = '3', senha='1234', email='3@xyz.com')
        p4 = Pessoa(nome = '4', senha='1234', email='4@xyz.com')
        p5 = Pessoa(nome = '5', senha='1234', email='5@xyz.com')
        p6 = Pessoa(nome = '6', senha='1234', email='6@xyz.com')
        p7 = Pessoa(nome = '7', senha='1234', email='7@xyz.com')
        p8 = Pessoa(nome = '8', senha='1234', email='8@xyz.com')

        # per??odo de apura????o = 2007-03-10 at?? 2007-04-09
        Morador(pessoa = p1, republica = r, entrada = date(2007, 2, 1))
        Morador(pessoa = p2, republica = r, entrada = date(2007, 3, 20))
        Morador(pessoa = p3, republica = r, entrada = date(2007, 2, 1), saida = date(2007, 3, 20))
        Morador(pessoa = p4, republica = r, entrada = date(2007, 3, 20), saida = date(2007, 4, 4))
        Morador(pessoa = p5, republica = r, entrada = date(2007, 4, 20))
        Morador(pessoa = p6, republica = r, entrada = date(2007, 4, 9), saida = date(2007, 5, 4))
        Morador(pessoa = p7, republica = r, entrada = date(2007, 2, 1), saida = date(2007, 3, 1))
        Morador(pessoa = p8, republica = r, entrada = date(2007, 2, 1), saida = date(2007, 3, 10))

        Session.commit()

        moradores = Morador.get_moradores(
                                        republica=r,
                                        data_inicial = date(2007, 3, 10),
                                        data_final = date(2007, 4, 9)
                                        )

        assert p1 in moradores
        assert p2 in moradores
        assert p3 in moradores
        assert p4 in moradores
        assert p5 not in moradores
        assert p6 in moradores
        assert p7 not in moradores
        assert p8 in moradores




    # desabilitado
    def _test_registrar_responsavel_telefone(self):
        r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), endereco = 'R. dos Bobos, n?? 0', latitude = 0, longitude = 0)

        p1 = Pessoa(nome = 'Andr??')
        p2 = Pessoa(nome = 'Marcos')

        m1 = Morador(pessoa = p1, republica = r, entrada = date(2007, 2, 1))
        m2 = Morador(pessoa = p2, republica = r, entrada = date(2007, 3, 20))
        Session.commit()

        r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
        r.registrar_responsavel_telefone(numero = 222, responsavel = m2)
        r.registrar_responsavel_telefone(numero = 333, responsavel = m2)
        Session.commit()
        Session.expunge_all()

        r = Republica.get_by(id = 1)
        m1 = Morador.get_by(pessoa_id = 1)
        m2 = Morador.get_by(pessoa_id = 2)
        t1 = TelefoneRegistrado.get_by(numero = 111, republica = r)
        t2 = TelefoneRegistrado.get_by(numero = 222, republica = r)
        t3 = TelefoneRegistrado.get_by(numero = 333, republica = r)

        assert t1 is not None
        assert t2 is not None
        assert t3 is not None
        assert t1.responsavel is m1
        assert t2.responsavel is m2
        assert t3.responsavel is m2

        r.registrar_responsavel_telefone(numero = 333, responsavel = m1)
        r.registrar_responsavel_telefone(numero = 111, responsavel = None)
        r.registrar_responsavel_telefone(numero = 777, responsavel = None)
        Session.commit()
        Session.expunge_all()

        r = Republica.get_by(id = 1)
        m1 = Morador.get_by(pessoa_id = 1)
        m2 = Morador.get_by(pessoa_id = 2)
        t1 = TelefoneRegistrado.get_by(numero = 111, republica = r)
        t2 = TelefoneRegistrado.get_by(numero = 222, republica = r)
        t3 = TelefoneRegistrado.get_by(numero = 333, republica = r)
        t4 = TelefoneRegistrado.get_by(numero = 777, republica = r)

        assert t1 is None
        assert t2.responsavel is m2
        assert t3.responsavel is m1
        assert t4 is None


    # desabilitado
    def _test_registrar_responsavel_telefone_2(self):
        '''
        Testa um problema que parece ser do Elixir para atulizar automaticamente uma lista de depend??ncias entre uma
        entidade e outra de uma rela????o has_many/one_to_many.

        N??o tenho certeza se a adi????o ?? lista deveria acontecer automaticamente.
        veja o post publicado no grupo do sqlelixir:
        http://groups.google.com/group/sqlelixir/browse_thread/thread/710e82c3ad586aab/03fc48b416a09fcf#03fc48b416a09fcf
        '''
        r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), endereco = 'R. dos Bobos, n?? 0', latitude = 0, longitude = 0)

        p1 = Pessoa(nome = 'Andr??')
        p2 = Pessoa(nome = 'Marcos')

        m1 = Morador(pessoa = p1, republica = r, entrada = date(2007, 2, 1))
        m2 = Morador(pessoa = p2, republica = r, entrada = date(2007, 3, 20))
        Session.commit()

        r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
        Session.commit()
        try:
            r.registrar_responsavel_telefone(numero = 111, responsavel = m1)
        except:
            assert False, 'Erro no registro do mesmo respons??vel repetidamente'

        r.registrar_responsavel_telefone(numero = 777, responsavel = m1)
        Session.commit()
        r.registrar_responsavel_telefone(numero = 777, responsavel = None)
        Session.commit()

        assert TelefoneRegistrado.get_by(numero = 777, republica = r) is None


    # desabilitado
    def _test_registrar_responsavel_telefone_3(self):
        '''
        Segue a mesma linha do teste 2
        '''
        r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), endereco = 'R. dos Bobos, n?? 0', latitude = 0, longitude = 0)

        p1 = Pessoa(nome = 'Andr??')
        p2 = Pessoa(nome = 'Marcos')

        m1 = Morador(pessoa = p1, republica = r, entrada = date(2007, 2, 1))
        m2 = Morador(pessoa = p2, republica = r, entrada = date(2007, 3, 20))
        Session.commit()

        r.registrar_responsavel_telefone(numero = 777, responsavel = m1)
        Session.commit()
        r.registrar_responsavel_telefone(numero = 777, responsavel = None)
        Session.commit()

        assert TelefoneRegistrado.get_by(numero = 777, republica = r) is None


    # desabilitado
    def _test_aluguel(self):
        r = Republica(nome = 'Teste1', data_criacao = date(2007, 4, 8), endereco = 'R. dos Bobos, n?? 0', latitude = 0, longitude = 0)

        Aluguel(valor = Decimal(100), data_cadastro = date(2007, 1, 1), republica = r)
        Aluguel(valor = Decimal(200), data_cadastro = date(2007, 2, 1), republica = r)

        Session.commit()
        Session.expunge_all()

        r = Republica.get_by()

        assert r.aluguel(date(2006, 12, 1)) == None
        assert r.aluguel(date(2007, 1, 1)) == Decimal(100)
        assert r.aluguel(date(2007, 1, 15)) == Decimal(100)
        assert r.aluguel(date(2007, 2, 1)) == Decimal(200)
        assert r.aluguel(date(2007, 3, 1)) == Decimal(200)
