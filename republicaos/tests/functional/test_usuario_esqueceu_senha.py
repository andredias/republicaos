# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, TrocaSenha, Session
from republicaos.lib.helpers import flash, url
from republicaos.lib.auth import set_user
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestUsuarioEsqueceuSenha(TestController):
    def test_1(self):
        email = 'xyz@abc.com.br'
        Pessoa(nome='Fulano', email=email, senha='1234')
        Pessoa(nome='Beltrano', email='1234@56787.com.br', senha='1234')
        Session.commit()
        
        # email não cadastrado
        response = self.app.post(
                        url=url(controller='pessoa', action='esqueci_senha'),
                        params={
                                'email':'abc@def.com.br'
                            },
                    )
        
        assert 'error' in response
        
        # usuário autenticado, email não cadastrado
        response = self.app.post(
                        url=url(controller='pessoa', action='esqueci_senha'),
                        params={
                                'email':'abc@def.com.br'
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        
        assert 'error' in response
        
        # email cadastrado
        response = self.app.post(
                        url=url(controller='pessoa', action='esqueci_senha'),
                        params={
                                'email':email
                            },
                        status=302
                    )
        
        log.debug('response.session: %s', response.session)
        assert 'info' in response.session['flash'][0]
        assert urlparse(response.response.location).path == url(controller='root', action='index')
        assert Pessoa.get_by(id=TrocaSenha.get_by().pessoa.id).email == email
