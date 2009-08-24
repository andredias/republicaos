# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, Fechamento, Session
from republicaos.model import Despesa, DespesaAgendada
from republicaos.lib.helpers import flash, url_for
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from babel.dates import format_date

import logging
log = logging.getLogger(__name__)

class TestMoradorLancaDespesa(TestController):
    def test_um(self):
        republica = Republica(nome='Mae Joana', 
                        data_criacao = date.today(),
                        logradouro = 'R. dos Bobos, n. 0',
                        cidade = 'Sumare',
                        uf = 'SP')

        Fechamento(data=date.today() + timedelta(days=30), republica=republica)

        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Morador(pessoa=p2, republica=republica, entrada=date.today())
        Session.commit()
        
        # acesso direto ao link, sem definir república
        response = self.app.get(url=url_for(controller='despesa', action='new'),
                                status=404)
        
        url=url_for(controller='despesa', action='new', republica_id='1')
                    
        # acesso ao link sem morador autenticado
        response = self.app.get(url=url, status=302)
        assert '/login' in response

        # acesso correto à URL
        response = self.app.get(url=url, extra_environ={str('REMOTE_USER'):str('1')})
        
        assert 'Fulano &lt;abc@xyz.com.br&gt;' in response
        assert '<input name="agendamento" type="checkbox" value="mensal"' in response
        assert '<form action="%s" method="post">' % url in response
        
        
        # lança despesa inválida:
        response = self.app.post(
                            url=url,
                            params={
                                    'pessoa_id' : '1',
                                    'tipo_id' : '1',
                                    'quantia' : '',
                                    'lancamento' : format_date(date.today() - timedelta(days=10)),
                                    'agendamento' : False,
                                    'termino' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'erro_quantia' in response
        assert 'erro_lancamento' in response
        assert str(response).count('erro_') == 2
        
        
        # lança despesa inválida: término dentro do intervalo
        response = self.app.post(
                            url=url,
                            params={
                                    'pessoa_id' : '2',
                                    'tipo_id' : '1',
                                    'quantia' : '100,45',
                                    'lancamento' : format_date(date.today()),
                                    'agendamento' : True,
                                    'termino' : format_date(date.today()),
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'erro_termino' in response
        assert str(response).count('erro_') == 1
        assert Despesa.get_by(pessoa_id=2) == None
        assert DespesaAgendada.get_by() == None
        
        
        # lança despesa inválida: quantia negativa
        response = self.app.post(
                            url=url,
                            params={
                                    'pessoa_id' : '1',
                                    'tipo_id' : '1',
                                    'quantia' : '-2,45',
                                    'lancamento' : format_date(date.today()),
                                    'agendamento' : False,
                                    'termino' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'erro_quantia' in response
        assert str(response).count('erro_') == 1
        assert Despesa.get_by(pessoa_id=1) == None
        assert DespesaAgendada.get_by() == None


        # lança despesa válida
        response = self.app.post(
                            url=url,
                            params={
                                    'pessoa_id' : '2',
                                    'tipo_id' : '1',
                                    'quantia' : '1,23',
                                    'lancamento' : format_date(date.today()),
                                    'agendamento' : False,
                                    'termino' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'class="info"' in response
        assert '$ 1,23' in response
        assert Despesa.get_by(lancamento=date.today(), pessoa_id=2, republica_id=1, quantia=1.23)
        assert DespesaAgendada.get_by() == None
        
        
        # lança despesa válida com agendamento, sem término
        response = self.app.post(
                            url=url,
                            params={
                                    'pessoa_id' : '2',
                                    'tipo_id' : '2',
                                    'quantia' : '12,34',
                                    'lancamento' : format_date(date.today()),
                                    'agendamento' : True,
                                    'termino' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'class="info"' in response
        assert '$ 12,34' in response
        assert Despesa.get_by(lancamento=date.today(), pessoa_id=2, republica_id=1, quantia=12.34)
        desp = DespesaAgendada.get_by(pessoa_id='2', tipo_id='2')
        assert len(DespesaAgendada.query.all()) == 1
        assert desp.proximo_lancamento == (date.today() + relativedelta(months=1))
        assert desp.termino == None


        # lança despesa válida com agendamento
        response = self.app.post(
                            url=url,
                            params={
                                    'pessoa_id' : '2',
                                    'tipo_id' : '3',
                                    'quantia' : '123,45',
                                    'lancamento' : format_date(date.today() + timedelta(days=1)),
                                    'agendamento' : True,
                                    'termino' : format_date(date.today() + relativedelta(months=3)),
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'class="info"' in response
        assert '$ 123,45' in response
        desp = Despesa.get_by(pessoa_id='2', tipo_id='3')
        assert desp.lancamento == date.today() + timedelta(days=1)
        assert len(DespesaAgendada.query.all()) == 2
        
        desp = DespesaAgendada.get_by(pessoa_id='2', tipo_id='3')
        assert desp.proximo_lancamento == (date.today() + relativedelta(months=1, days=1)), desp.proximo_lancamento
        assert desp.termino == date.today() + relativedelta(months=3)
