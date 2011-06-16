# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, CadastroPendente, Session
from republicaos.lib.helpers import flash, url
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestPessoaSeCadastra(TestController):
    def test_dados_invalidos(self):
        """
        Testa se o uso de dados inválidos no cadastro resulta em mensagens de erro
        """
        response = self.app.post(
            url=url(controller='pessoa', action='new'),
            params={
                'email': 'abcdefg',
#               'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '5678',
                'captcha': '3',
                'captcha_md5' : 'c81e728d9d4c2f636f067f89cc14862c',
#               'aceito_termos': '1',
            }
        )

        assert str(response).count('class="error"') == 1
        assert 'email: Um endereço de email deve conter apenas uma @' in response
        assert 'nome: Missing value' in response
        assert 'confirmacao_senha: Os campos não são iguais' in response
        assert 'aceito_termos: Missing value' in response
        assert 'captcha: Resposta incorreta' in response
    
    
    def test_email_ja_cadastrado(self):
        """
        Usa um endereço de e-mail já cadastrado no sistema
        """
        Pessoa(nome='user1', senha='1234', email='suporte@pronus.eng.br')
        Session.commit()
        
        response = self.app.post(
            url=url(controller='pessoa', action='new'),
            params={
                'email': 'suporte@pronus.eng.br',
                'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '1234',
                'aceito_termos': '1',
                'captcha':'2',
                'captcha_md5' : 'c81e728d9d4c2f636f067f89cc14862c',
            }
        )
        
        assert str(response).count('class="error"') == 1
        assert 'email: Valor ja registrado no banco de dados' in response


    def test_email_com_cadastrado_pendente(self):
        """
        Usa um endereço de e-mail que já tem pedido de cadastro pendente
        """
        CadastroPendente(nome='Fulano', email='abc@xyz.com', senha='1234')
        Session.commit()
        
        response = self.app.post(
            url=url(controller='pessoa', action='new'),
            params={
                'email': 'suporte@pronus.eng.br',
                'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '1234',
                'aceito_termos': '1',
                'captcha':'2',
                'captcha_md5' : 'c81e728d9d4c2f636f067f89cc14862c',
            }
        )
        assert 'mensagem de ativação do cadastro foi enviada' in response.session['flash'][-1][1]
    
    
    def test_dados_validos(self):
        '''
        Testa resultado com todos os dados válidos
        '''
        response = self.app.post(
            url=url(controller='pessoa', action='new'),
            params={
                'email': 'suporte@pronus.eng.br',
                'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '1234',
                'aceito_termos': '1',
                'captcha': '2',
                'captcha_md5' : 'c81e728d9d4c2f636f067f89cc14862c',
            },
            # status esperado. Verifica automaticamente. Veja
            # http://pylonsbook.com/en/1.0/testing.html#functional-testing
            status = 302
        )
        assert 'mensagem de ativação do cadastro foi enviada' in response.session['flash'][-1][1]
        assert CadastroPendente.get_by(email='suporte@pronus.eng.br')
        # Verificar se a resposta redireciona para a página inicial
        assert urlparse(response.response.location).path == url(controller='root', action='index')


