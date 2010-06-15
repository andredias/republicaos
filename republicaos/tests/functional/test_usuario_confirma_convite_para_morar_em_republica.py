# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, ConviteMorador, Session
from republicaos.lib.helpers import flash, url
from datetime import date, datetime, timedelta
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestUsuarioConfirmaConviteParaMorador(TestController):
    def test_um(self):
        ontem = date.today() - timedelta(days=1)
        mes_passado = date.today() - timedelta(days=30)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        Session.commit() # para garantir que o id de p2 é 2
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        republica = Republica(nome='Mae Joana', 
                        data_criacao = mes_passado,
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        convite1 = ConviteMorador(nome=p2.nome, email=p2.email, republica=republica, user=p1)
        convite2 = ConviteMorador(nome='Siclano', email='siclano@republicaos.com.br', republica=republica, user=p1)
        Session.commit()
        
        link1 = convite1.link_confirmacao
        link2 = convite2.link_confirmacao
        link_invalido = link1[:-10]
        
        # link inexistente
        response = self.app.post(url=link_invalido)
        assert 'Link Inválido' in response
        
        
        # verificação da resposta da confirmação do convite a usuário cadastrado
        response = self.app.post(url=link1)
        assert 'confirmacao_senha' not in response
        assert 'Beltrano' in response
        assert response.session['userid'] == 2

        
        # verificação da resposta da confirmação do convite a usuário não-cadastrado
        response = self.app.post(url=link2)
        assert 'confirmacao_senha' in response
        assert 'Siclano' in response
        assert '<input class="text" name="nome"' in response

        
        # confirmação do convite a usuário cadastrado com data de entrada inválida
        response = self.app.post(url=link1,
                            params = {
                                    'entrada' : (mes_passado - timedelta(days=1)).strftime('%d/%m/%Y')
                                    }
                            )
        assert 'erro_entrada' in response
        assert response.session.get('flash') is None
        assert ConviteMorador.get_by(hash=link1[-40:])
        
        
        # confirmação do convite a usuário cadastrado com data de entrada válida
        response = self.app.post(url=link1,
                            params = {
                                    'entrada' : mes_passado.strftime('%d/%m/%Y')
                                    }
                            )
        assert Morador.get_by(pessoa_id=2, republica_id=1, entrada=mes_passado)
        assert ConviteMorador.get_by(hash=link1[-40:]) is None
        assert 'Bem vindo' in response.session['flash'][-1][1]
        
        # convite à pessoa não cadastrada
        assert ConviteMorador.get_by(hash=link2[-40:])
        response = self.app.post(url=link2,
                            params = {
                                    'nome' : 'Siclano da Silva',
                                    'senha' : '1234',
                                    'confirmacao_senha' : '1234',
                                    'entrada' : mes_passado.strftime('%d/%m/%Y'),
                                    'aceito_termos': '1'
                                    }
                            )
        assert Pessoa.get_by(email='siclano@republicaos.com.br')
        assert Morador.get_by(pessoa_id=3, republica_id=1, entrada=mes_passado)
        assert 'Bem vindo' in response.session['flash'][-1][1]
        assert ConviteMorador.get_by(hash=link2[-40:]) is None
        
        
