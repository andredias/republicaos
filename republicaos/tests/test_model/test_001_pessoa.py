#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
from sqlalchemy.exceptions import IntegrityError
from republicaos.tests import Session, TestModel
from republicaos.model import Pessoa, Republica, Fechamento, Morador
from datetime   import date, time, timedelta
from decimal import Decimal

class TestPessoa(TestModel):
    def test_criacao(self):
        p = Pessoa(nome = 'Andre', senha='1234', email='abc@xyz.com')

        Session.commit()
        Session.expunge_all()

        x = Pessoa.get_by()
        assert x.nome == 'Andre'


    def test_criptografia_senha(self):
        pass


    def test_qts_dias_morados(self):
        '''
        Quantos dias uma pessoa morou na república
        '''
        r = Republica(nome = 'Pronus',
                logradouro = 'Av. Ipe Amarelo, 320 c. 21',
                cidade = 'Sumare',
                uf = 'SP',
                data_criacao = date(2007, 1, 1)
            )
        p = Pessoa(nome = 'André', senha='123', email='abc@xyz.com')

        Morador(pessoa = p, republica = r, entrada = date(2007, 5, 8), saida = date(2007, 6, 10))
        # morou mais de uma vez na mesma república
        Morador(pessoa = p, republica = r, entrada = date(2009, 1, 1), saida = date(2009, 7, 13))

        Session.commit()

        assert p.get_qtd_dias_morados(r, date(2007, 4, 8), date(2007, 5, 7)) == 0
        assert p.get_qtd_dias_morados(r, date(2007, 5, 8), date(2007, 6, 7)) == 31
        assert p.get_qtd_dias_morados(r, date(2007, 6, 8), date(2007, 7, 7)) == 3

        # saiu
        assert p.get_qtd_dias_morados(r, date(2007, 7, 8), date(2007, 8, 7)) == 0

        # voltou a morar
        assert p.get_qtd_dias_morados(r, date(2009, 6, 5), date(2009, 7, 4)) == 30

        # período total
        assert p.get_qtd_dias_morados(r) == 228


    def test_morador_em_republica(self):
        r1 = Republica(nome = 'Pronus',
                logradouro = 'Av. Ipe Amarelo, 320 c. 21',
                cidade = 'Sumare',
                uf = 'SP',
                data_criacao = date(2007, 1, 1)
            )
        r2 = Republica(nome = 'Mae Joana',
                logradouro = 'Av. Ipe Amarelo, 320 c. 21',
                cidade = 'Sumare',
                uf = 'SP',
                data_criacao = date(2009, 8, 13)
            )
        p1 = Pessoa(nome = 'André', senha='123', email='abc@xyz.com')
        p2 = Pessoa(nome = 'Felipe', senha='123', email='felipe@xyz.com')
        p3 = Pessoa(nome = 'Dias', senha='123', email='dias@xyz.com')

        Morador(pessoa=p1, republica=r1, entrada=date(2007, 1, 1), saida=date(2007, 10, 1))
        Morador(pessoa=p1, republica=r2, entrada=date(2007, 10, 1))
        Morador(pessoa=p2, republica=r1, entrada=date(2008, 1, 1), saida=date.today())
        Morador(pessoa=p2, republica=r2, entrada=date.today(), saida=date.today() + timedelta(days=10))
        Morador(pessoa=p3, republica=r2, entrada=date.today() + timedelta(days=1), saida=date.today() + timedelta(days=30))
        
        Session.commit()
        
        r1._preencher_fechamentos()
        r2._preencher_fechamentos()


        assert r1 not in p1.morador_em_republicas
        assert r1 in p1.ex_morador_em_republicas
        assert r1 in p2.morador_em_republicas
        assert r2 in p2.morador_em_republicas
        assert len(p3.morador_em_republicas) == 0





