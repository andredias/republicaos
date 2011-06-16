# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, CadastroPendente, Session
from republicaos.lib.helpers import flash, url
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)


class TestUsuarioConfirmaCadastro(TestController):

    
    def test_link_invalido(self):
        '''
        O link para confirmar o cadastro pendente é inválido
        '''
        cp = CadastroPendente(nome='Fulano', email='abc@xyz.com', senha='1234')
        CadastroPendente(nome='Beltrano', email='beltrano@xyz.com', senha='1234')
        Session.commit()
        link = cp.link_confirmacao[:-10] # produzindo um link inválido
        response = self.app.get(url=link)
        
        assert response.body.count('class="error"') == 1
        assert 'O link fornecido para confirmação de cadastro não é válido' in response
        
        
    def test_link_valido(self):
        '''
        O link para confirmar o cadastro pendente é inválido
        '''
        cp = CadastroPendente(nome='Fulano', email='abc@xyz.com', senha='1234')
        Session.commit()
        link = cp.link_confirmacao
        
        response = self.app.get(url=link)
        assert response.session.get('userid') == Pessoa.get_by().id
        assert CadastroPendente.get_by() is None
        
        
        
        
