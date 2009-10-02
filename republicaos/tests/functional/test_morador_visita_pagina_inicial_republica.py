# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, Fechamento, Session
from republicaos.lib.helpers import flash, url_for
from republicaos.lib.auth import set_user
from urlparse import urlparse
from datetime import date, timedelta

import logging
log = logging.getLogger(__name__)

class TestMoradorVisitaPaginaInicialRepublica(TestController):
    def test_um(self):
        republica = Republica(nome='Jerônimo', 
                        data_criacao = date.today(),
                        endereco = 'R. Jeronimo Pattaro, 186, Campinas, SP',
                        latitude = 0,
                        longitude = 0)

        Fechamento(data=date.today() + timedelta(days=30), republica=republica)

        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Morador(pessoa=p2, republica=republica, entrada=date.today())
        Session.commit()
        
        response = self.app.get(
                            url=url_for(
                                        controller='republica',
                                        action='show',
                                        republica_id='1'
                                    ), 
                            extra_environ={str('REMOTE_USER'):str('1')}
                        )
        assert 'Fulano &lt;abc@xyz.com.br&gt;' in response
        assert 'Beltrano &lt;beltrano@republicaos.com.br&gt;' in response
        assert 'Latitude: ' in response
