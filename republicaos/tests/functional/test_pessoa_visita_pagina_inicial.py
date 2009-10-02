# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Session
from republicaos.lib.helpers import flash, url_for
from republicaos.lib.auth import set_user
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestPessoaVisitaPaginaInicial(TestController):
    def test_pessoa_nao_autenticada(self):
        """
        Testa visita de pessoa não autenticada na página inicial
        """
        response = self.app.get(url=url_for(controller='root', action='index'))
        assert 'id="userinfo"' not in response
    
    
    def test_pessoa_autenticada(self):
        """
        Testa visita de pessoa autenticada na página inicial
        """
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        Session.commit()
        response = self.app.get(
                            url=url_for(controller='root', action='index'), 
                            extra_environ={str('REMOTE_USER'):str('1')}
                        )
        assert 'Fulano &lt;abc@xyz.com.br&gt;' in response
