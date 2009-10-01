# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Republica, Fechamento, Pessoa, Morador, Session
from republicaos.lib.helpers import flash, url_for
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from babel.dates import format_date

import logging
log = logging.getLogger(__name__)

class TestMoradorCRUDFechamento(TestController):
    def setUp(self):
        TestController.setUp(self)
        republica = Republica(nome='Mae Joana', 
                        data_criacao = date.today() - relativedelta(months=2),
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Fechamento(republica=republica, data=date.today() - relativedelta(months=1))
        Fechamento(republica=republica, data=date.today())
        Fechamento(republica=republica, data=date.today() + relativedelta(months=1))
        Session.commit()
        
        
    def test_autenticacao_autorizacao(self):
        # acesso direto ao link, sem definir república
        response = self.app.get(url=url_for(controller='fechamento', action='new'),
                                status=404)
        response = self.app.get(
                url=url_for(controller='fechamento', action='edit', data=date.today()),
                status=404
                )
        response = self.app.get(
                url=url_for(controller='fechamento', action='delete', data=date.today()),
                status=404
                )
                    
        # acesso ao link sem morador autenticado
        response = self.app.get(
                    url=url_for(controller='fechamento', action='new', republica_id='1'),
                    status=302
                )
        assert '/login' in response

        response = self.app.get(
                    url=url_for(
                            controller='fechamento',
                            action='edit',
                            data=date.today(),
                            republica_id='1'
                            ),
                    status=302
                )
        assert '/login' in response
        
        response = self.app.get(
                    url=url_for(
                            controller='fechamento',
                            action='delete',
                            data=date.today(),
                            republica_id='1'
                            ),
                    status=302
                )
        assert '/login' in response


    def test_new_fechamento(self):
        url = url_for(controller='fechamento', action='new', republica_id='1')
        response = self.app.get(
                    url=url,
                    extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'Criar Fechamento' in response
        
        # data inválida: data = data da criação
        response = self.app.post(
                        url=url,
                        params={'data':format_date(date.today() - relativedelta(months=2))},
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'erro_data' in response
        assert Fechamento.get_by(data=date.today() - relativedelta(months=2), republica_id='1') == None
        
        # data inválida: data de fechamento que já existe
        # TODO: tratamento de BD
#        response = self.app.post(
#                        url=url,
#                        params={'data':date.today()},
#                        extra_environ={str('REMOTE_USER'):str('1')}
#                    )
#        assert '(erro)' in response.session['flash'][0]
        
        # data válida: data antes da data da criação
        response = self.app.post(
                        url=url,
                        params={'data':format_date(date.today() + relativedelta(weeks=2))},
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert '(info) Fechamento criado com sucesso' in response.session['flash'][0]
        assert Fechamento.get_by(data=date.today() + relativedelta(weeks=2), republica_id='1')
        
        
    
    
    def test_edit_fechamento(self):
        url = url_for(
                controller='fechamento',
                action='edit',
                republica_id='1',
                data=date.today()
                )
        
        response = self.app.get(
                    url=url,
                    extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'Editar Fechamento' in response
        
        # data inválida: data = data da criação
        response = self.app.post(
                        url=url,
                        params={'data':format_date(date.today() - relativedelta(months=2))},
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'erro_data' in response
        assert Fechamento.get_by(data=date.today() - relativedelta(months=2), republica_id='1') == None
        
        
        # data inválida: data de outro fechamento que já existe
        # TODO: teste de tratamento de bd
#        response = self.app.post(
#                        url=url,
#                        params={'data':format_date(date.today() + relativedelta(months=1))},
#                        extra_environ={str('REMOTE_USER'):str('1')}
#                    )
#        assert '(erro)' in response.session['flash'][0]
        
        # data válida: data antes da data da criação
        response = self.app.post(
                        url=url,
                        params={'data':format_date(date.today() + relativedelta(weeks=2))},
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert '(info) Data do fechamento alterada com sucesso' in response.session['flash'][0]
        assert Fechamento.get_by(data=date.today() + relativedelta(weeks=2), republica_id='1') != None
    
    
    def test_delete_fechamento(self):
        url = url_for(
                controller='fechamento',
                action='delete',
                republica_id='1',
                data=date.today()
                )
        
        # TODO: acessar a url através de método DELETE
        # exclui fechamento de hoje
        response = self.app.post(
                    url=url,
                    extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert '(info) Fechamento excluído com sucesso' in response.session.pop('flash')[0]
        assert Fechamento.get_by(data=date.today(), republica_id='1') == None
        
        
        # exclui a mesma data de novo. A data não existe mais!
        response = self.app.post(
                        url=url,
                        extra_environ={str('REMOTE_USER'):str('1')},
                        status=404
                    )

        # tenta excluir último fechamento futuro
        url = url_for(
                controller='fechamento',
                action='delete',
                republica_id='1',
                data=date.today() + relativedelta(months=1)
                )
        
        response = self.app.post(
                        url=url,
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert '(error) Não foi possível excluir o fechamento' in ''.join(response.session['flash'])
        assert Fechamento.get_by(data=date.today() + relativedelta(months=1), republica_id='1')
        
        Fechamento(data=date.today() + relativedelta(weeks=2), republica_id='1')
        Session.commit()

        # agora deve ser possível excluir último fechamento
        response = self.app.post(
                        url=url,
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert '(info) Fechamento excluído com sucesso' in response.session['flash'][0]
        assert Fechamento.get_by(data=date.today() + relativedelta(months=1), republica_id='1') == None
