# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, TrocaSenha, Session
from republicaos.lib.helpers import flash, url
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)


class TestUsuarioConfirmaTrocaSenha(TestController):

    
    def test_1(self):
        '''
        O link para confirmar o cadastro pendente é inválido
        '''
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com', senha='1234')
        Session.commit() # pra garantir id = 1
        p2 = Pessoa(nome='Beltrano', email='beltrano@xyz.com', senha='1234')
        ts1 = TrocaSenha(pessoa=p1)
        ts2 = TrocaSenha(pessoa=p2)
        Session.commit()
        
        link = ts1.link_confirmacao[:-10] # produzindo um link inválido
        response = self.app.get(url=link)
        assert 'O link fornecido para troca de senha não é válido' in response
        

        link = ts1.link_confirmacao
        response = self.app.get(url=link)
        
        assert response.session.get('userid') == 1
        assert TrocaSenha.get_by(pessoa_id=1) is None
        assert TrocaSenha.get_by(pessoa_id=2)
        assert urlparse(response.response.location).path == url(
                                                        controller='pessoa', action='edit', id=1)
        
        
        
        
