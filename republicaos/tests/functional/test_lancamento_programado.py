# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, Fechamento, Session
from republicaos.model import Despesa, DespesaAgendada, TipoDespesa
from republicaos.lib.helpers import flash, url
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from babel.dates import format_date

import logging
log = logging.getLogger(__name__)

class TestLancamentoProgramado(TestController):
    '''
    Testa edição e exclusão de lançamento programado. A criação já é feita durante a criação da despesa.
    '''
    def test_um(self):
        republica = Republica(nome='Mae Joana', 
                        data_criacao = date.today(),
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)

        Fechamento(data=date.today() + timedelta(days=30), republica=republica)

        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Morador(pessoa=p2, republica=republica, entrada=date.today())
        Session.commit()
        
        DespesaAgendada(
                    proximo_lancamento=date.today() + relativedelta(months=1),
                    quantia = 99,
                    repeticoes = 5,
                    pessoa = p2,
                    republica = republica,
                    tipo = republica.tipos_despesa[0]
                    )
        DespesaAgendada(
                    proximo_lancamento=date.today() + relativedelta(weeks=2),
                    quantia = 100,
                    pessoa = p1,
                    republica = republica,
                    tipo = republica.tipos_despesa[1]
                    )
        Session.commit()
        
        # acesso direto ao link, sem definir república
        response = self.app.get(url=url(controller='lancamento_programado', action='edit', id=1),
                                status=404)
        
        url_=url(controller='lancamento_programado', action='edit', republica_id='1', id = 1)
                    
        # acesso ao link sem morador autenticado
        response = self.app.get(url=url_, status=302)
        assert '/login' in response

        # acesso correto à URL
        response = self.app.get(url=url_, extra_environ={str('REMOTE_USER'):str('1')})
        
        assert 'Fulano &lt;abc@xyz.com.br&gt;' in response
        assert '<input name="agendamento"' not in response
        assert '<input name="repeticoes"' in response
        
        
        # edita lançamento inválida:
        response = self.app.post(
                            url=url_,
                            params={
                                    'pessoa_id' : '1',
                                    'tipo_id' : '1',
                                    'quantia' : '',
                                    'lancamento' : format_date(date.today() - relativedelta(months=1)),
                                    'repeticoes' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'erro_quantia' in response
        assert 'erro_lancamento' in response
        assert str(response).count('erro_') == 2
        
        
        # lança despesa inválida: quantia negativa e repeticoes < 1
        response = self.app.post(
                            url=url_,
                            params={
                                    'pessoa_id' : '1',
                                    'tipo_id' : '2',
                                    'quantia' : '-2,45',
                                    'lancamento' : format_date(date.today()),
                                    'repeticoes' : '0',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'erro_quantia' in response
        assert 'erro_repeticoes' in response
        assert str(response).count('erro_') == 2


        # lança despesa com término dentro do intervalo
        response = self.app.post(
                            url=url_,
                            params={
                                    'pessoa_id' : '2',
                                    'tipo_id' : '1',
                                    'quantia' : '101',
                                    'lancamento' : format_date(date.today()),
                                    'repeticoes' : '2',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert str(response).count('erro_') == 0
        despesa = DespesaAgendada.get_by(id=1)
        assert despesa.quantia == 101
        assert despesa.proximo_lancamento == date.today()
        assert despesa.repeticoes == 2
        
        
        # exclusão de despesa agendada
        response = self.app.post(
                            url=url(
                                    controller='lancamento_programado',
                                    action='delete',
                                    republica_id=1,
                                    id=1
                                    ),
                            extra_environ={str('REMOTE_USER'):str('2')},
                            status=302
                            )
        assert DespesaAgendada.get_by(id=1) == None
