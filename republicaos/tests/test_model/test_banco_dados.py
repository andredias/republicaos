#!/usr/bin/python
# -*- coding: utf-8 -*-

from base import BaseTest
from republicaos.model.model import *
from elixir import session, metadata, setup_all
from decimal import Decimal

'''
A finalidade desses testes é garantir que o tipo Money criado para lidar com Decimal no SQLite funcione também
no Postgres.
'''

class BaseBancoDeDados(BaseTest):
    def setup(self):
        if metadata.bind != self.url:
            metadata.bind = self.url
            setup_all()
        BaseTest.setup(self)

    def popula_dados(self):
        r = Republica(nome = 'Teste',
            data_criacao = date.today(),
            logradouro = 'R. dos Bobos, nº 0')
        
        c = ContaTelefone(
                telefone = 1111,
                id_operadora = 1,
                emissao = date(2007, 4, 29),
                vencimento = date(2007, 5, 10),
                republica = r,
                franquia  = Decimal('12.23'),
                servicos = Decimal(10)
                )
        session.commit()
        session.clear()
        
    
    def test_recuperacao(self):
        self.popula_dados()
        
        r = Republica.get_by(id = 1)
        c = ContaTelefone.get_by(id = 1)
        
        assert c.franquia == Decimal('12.23')
        assert c.servicos == Decimal(10)



class TestSQLite(BaseBancoDeDados):
    url = 'sqlite:///:memory:'


#class TestPostgres(BaseBancoDeDados):
#    url = 'postgres://turbo_gears:tgears@localhost/tg_teste'
