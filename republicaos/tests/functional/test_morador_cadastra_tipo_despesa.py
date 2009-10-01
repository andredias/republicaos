# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, Session
from republicaos.model import Despesa, TipoDespesa
from republicaos.lib.helpers import flash, url_for
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from babel.dates import format_date

import logging
log = logging.getLogger(__name__)

class TestMoradorCadastraTipoDespesa(TestController):
    def test_um(self):
        republica = Republica(nome='Mae Joana', 
                        data_criacao = date.today(),
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Session.commit()
        
        # acesso direto ao link, sem definir república
        response = self.app.get(url=url_for(controller='tipo_despesa', action='new'),
                                status=404)
        
        url=url_for(controller='tipo_despesa', action='new', republica_id='1')
                    
        # acesso ao link sem morador autenticado
        response = self.app.get(url=url, status=302)
        assert '/login' in response

        # acesso correto à URL
        response = self.app.get(url=url, extra_environ={str('REMOTE_USER'):str('1')})
        
        assert 'Novo Tipo de Despesa' in response
        
        
        # lança tipo de despesa inválida:
        response = self.app.post(
                            url=url,
                            params={
                                    'nome' : '',
                                    'descricao' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert 'erro_nome' in response
        assert str(response).count('erro_') == 1
        
        
        # cadastra tipo de despesa válida:
        response = self.app.post(
                            url=url,
                            params={
                                    'nome' : 'Internet',
                                    'descricao' : '',
                                    },
                            extra_environ={str('REMOTE_USER'):str('1')}
                            )
        assert '(info) Tipo de Despesa criado: Internet' in ''.join(response.session['flash'])
        assert TipoDespesa.get_by(nome='Internet', republica_id='1')
        
                
        # TODO: implementar
        # cadastra tipo de despesa com mesmo nome:
#        response = self.app.post(
#                            url=url,
#                            params={
#                                    'nome' : 'Internet',
#                                    'descricao' : '',
#                                    },
#                            extra_environ={str('REMOTE_USER'):str('1')}
#                            )
#        assert '(info) Tipo de Despesa criado: Internet' in ''.join(response.session['flash'])


