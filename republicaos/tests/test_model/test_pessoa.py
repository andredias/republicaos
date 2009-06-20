#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
from sqlalchemy.exceptions import IntegrityError
from republicaos.tests import Session, TestModel
from republicaos.model import Pessoa, Republica, Fechamento, ContaTelefone
from datetime   import date, time
from decimal import Decimal

class TestPessoa(TestModel):
    def test_criacao(self):
        p = Pessoa(nome = 'Andre')
        
        Session.commit()
        Session.expunge_all()
        
        x = Pessoa.get_by()
        assert x.nome == 'Andre'
