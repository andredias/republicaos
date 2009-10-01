# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, Fechamento, Session
from republicaos.model import Despesa, DespesaAgendada, TipoDespesa
from republicaos.lib.helpers import flash, url_for
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from babel.dates import format_date

import logging
log = logging.getLogger(__name__)

class TestMoradorExcluiDespesa(TestController):
    def test_um(self):
        republica = Republica(nome='Mae Joana', 
                        data_criacao = date.today(),
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        

        Fechamento(data=date.today() + timedelta(days=30), republica=republica)

        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Session.commit()
        
        tipos = TipoDespesa.query.filter(TipoDespesa.republica==republica).all()
        Despesa(lancamento=date.today(), pessoa=p1, republica=republica, quantia=100.23, tipo=tipos[0])
        Session.commit()
        
        republica2 = Republica(nome='Jeronimo', 
                        data_criacao = date.today() - relativedelta(months=1),
                        endereco = 'R. Jeronimo Pataro, Campinas, SP',
                        latitude = 0,
                        longitude = 0)
        
        Fechamento(data=date.today() - relativedelta(weeks=2), republica=republica2)
        Fechamento(data=date.today(), republica=republica2)
        Fechamento(data=date.today() + relativedelta(months=1), republica=republica2)
        
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        Morador(pessoa=p2, republica=republica2, entrada=republica2.data_criacao)
        Session.commit()
        
        tipos = TipoDespesa.query.filter(TipoDespesa.republica==republica2).all()
        Despesa(
                lancamento=date.today() - relativedelta(months=1),
                pessoa=p2,
                republica=republica2,
                quantia=9.50,
                tipo=tipos[1]
                )
        Session.commit()
        Despesa(
                lancamento=date.today(),
                pessoa=p2,
                republica=republica2,
                quantia=1.99,
                tipo=tipos[2]
                )
        Session.commit()
        
        # Tenta excluir uma despesa inexistente
        url = url_for(controller='despesa', action='delete', republica_id='2', id='100')
        response = self.app.post(
                            url=url,
                            extra_environ={str('REMOTE_USER'):str('2')},
                            status=404
                        )
        
        # Tenta excluir despesa de outra república
        url = url_for(controller='despesa', action='delete', republica_id='2', id='2')
        response = self.app.post(
                            url=url,
                            extra_environ={str('REMOTE_USER'):str('1')},
                            status=403
                        )
        
        # Tenta excluir uma despesa fora da data do fechamento corrente
        response = self.app.post(
                            url=url,
                            extra_environ={str('REMOTE_USER'):str('2')},
                        )
        assert '(error)' in ''.join(response.session['flash'])

        
        
        # Excluir uma despesa válida
        url = url_for(controller='despesa', action='delete', republica_id='2', id='3')
        response = self.app.post(
                            url=url,
                            extra_environ={str('REMOTE_USER'):str('2')},
                        )
        assert '(info) Despesa removida' in ''.join(response.session['flash'])
        assert Despesa.get_by(id=3) == None
