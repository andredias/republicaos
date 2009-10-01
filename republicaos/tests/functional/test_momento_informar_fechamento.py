# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Republica, Fechamento, Pessoa, Morador, Session
from republicaos.lib.helpers import flash, url_for
from republicaos.lib.mail import log
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from babel.dates import format_date

class TestMomentoInformarFechamento(TestController):
    def test_um(self):
        mes_retrasado = date.today() - relativedelta(months=2)
        mes_passado = date.today() - relativedelta(months=1)
        hoje = date.today()
        mes_que_vem = date.today() + relativedelta(months=1)
        
        r1 = Republica(nome='Mae Joana', 
                        data_criacao = mes_retrasado,
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
                        
        r2 = Republica(nome='Jeronimo', 
                        data_criacao = mes_retrasado,
                        endereco = 'Av. Ipê Amarelo, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='123@xyz.com.br', senha='1234')
        p3 = Pessoa(nome='Siclano', email='siclano@xyz.com.br', senha='1234')
        
        Morador(pessoa=p1, republica=r1, entrada=mes_retrasado)
        Morador(pessoa=p2, republica=r1, entrada=mes_retrasado)
        
        Morador(pessoa=p2, republica=r2, entrada=mes_retrasado)
        Morador(pessoa=p3, republica=r2, entrada=mes_passado)
        
        
        Fechamento(republica=r1, data=mes_passado)
        Fechamento(republica=r1, data=hoje)
        
        Fechamento(republica=r2, data=mes_passado)
        Fechamento(republica=r2, data=hoje)
        Session.commit()
        
        Fechamento.momento_informar_fechamentos()
        # TODO: como ver se mandou e-mail?
        assert Fechamento.get_by(republica=r1, data=mes_que_vem)
        assert Fechamento.get_by(republica=r2, data=mes_que_vem)
