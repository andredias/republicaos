# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import *
from republicaos.model import Pessoa, CadastroPendente, Session
from republicaos.lib.helpers import flash, url_for
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestPessoaSeCadastra(TestController):
    def test_dados_invalidos(self):
        """
        Testa se o uso de dados inválidos no cadastro resulta em mensagens de erro
        """
        response = self.app.post(
            url=url_for(controller='pessoa', action='new'),
            params={
                'email': 'abcdefg',
#               'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '5678',
#               'aceito_termos': '1',
            }
        )

        assert str(response).count('class="error-message"') == 4
        assert 'erro_email' in response
        assert 'erro_nome' in response
        assert 'erro_confirmacao_senha' in response
        assert 'erro_aceito_termos' in response
    
    
    def test_email_ja_cadastrado(self):
        """
        Usa um endereço de e-mail já cadastrado no sistema
        """
        Pessoa(nome='user1', senha='1234', email='suporte@pronus.eng.br')
        Session.commit()
        
        response = self.app.post(
            url=url_for(controller='pessoa', action='new'),
            params={
                'email': 'suporte@pronus.eng.br',
                'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '1234',
                'aceito_termos': '1',
            }
        )
        
        assert str(response).count('class="error-message"') == 1
        assert 'erro_email' in response


    def test_email_com_cadastrado_pendente(self):
        """
        Usa um endereço de e-mail que já tem pedido de cadastro pendente
        """
        CadastroPendente(nome='user1', senha='1234', email='suporte@pronus.eng.br')
        Session.commit()
        
        response = self.app.post(
            url=url_for(controller='pessoa', action='new'),
            params={
                'email': 'suporte@pronus.eng.br',
                'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '1234',
                'aceito_termos': '1',
            }
        )
        messages = ' '.join(response.session['flash'])
        assert 'Já existe um pedido de cadastro pendente para o e-mail fornecido.' in messages
        assert 'Uma mensagem de ativação do cadastro foi enviada para o e-mail fornecido' in messages
    
    
    def test_dados_validos(self):
        '''
        Testa resultado com todos os dados válidos
        '''
        response = self.app.post(
            url=url_for(controller='pessoa', action='new'),
            params={
                'email': 'suporte@pronus.eng.br',
                'nome': 'Nome com Acentuação',
                'senha': '1234',
                'confirmacao_senha': '1234',
                'aceito_termos': '1',
            },
            # status esperado. Verifica automaticamente. Veja
            # http://pylonsbook.com/en/1.0/testing.html#functional-testing
            status = 302
        )
         # junta todas as mensagens pra facilitar a busca
        messages = ' '.join(response.session['flash'])
        assert 'Uma mensagem de ativação do cadastro foi enviada para o e-mail fornecido.' in messages
        assert CadastroPendente.get_by(email='suporte@pronus.eng.br')
        # Verificar se a resposta redireciona para a página inicial
        assert urlparse(response.response.location).path == url_for(controller='root', action='index')



