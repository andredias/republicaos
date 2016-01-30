# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, CadastroPendente, Session
from republicaos.lib.helpers import flash, url
from datetime import date, datetime, timedelta
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)


class TestUsuarioConfirmaCadastro(TestController):

    def test_link_invalido(self):
        '''
        O link para confirmar o cadastro pendente é inválido
        '''
        cp = CadastroPendente(email='abc@xyz.com')
        Session.commit()
        link = cp.link_confirmacao[:-10] # produzindo um link inválido
        response = self.app.get(url=link)
        
        assert response.body.count('class="error"') == 1
        assert 'O link fornecido para confirmação de cadastro não é válido' in response
        
        
    def test_link_valido(self):
        '''
        O link para confirmar o cadastro pendente é inválido
        '''
        cp = CadastroPendente(email='abc@xyz.com')
        Session.commit()
        link = cp.link_confirmacao
        
        response = self.app.get(url=link)
        assert response.session.get('userid') == Pessoa.get_by().id
        assert CadastroPendente.get_by() is None
        
        
    def test_ativacao_cadastro_completo(self):
        '''
        Pessoa fornece dados incompletos para link válido de ativação
        '''
        
        email = 'abc@xyz.com'
        cp = CadastroPendente(email=email)
        Session.commit()
        link = cp.link_confirmacao
        
        response = self.app.post(url=link,
                                params={
                                        'nome': 'Teste ABC',
                                        'senha': '1234',
                                        'confirmacao_senha': '5678',
                                        'aceito_termos': '1',
                                        'criar_nova_republica': '1',
                                        'nome_republica': 'Jeronimo',
                                        'enviar_convites_para': 'andref.dias@gmail.com\nbarao_cps@hotmail.com\n',
                                        }
                                )
        
        # assert user.email = email do cadastro pendente
        assert CadastroPendente(email=email) is None
        pessoa = Pessoa.get_by(email=email)
        assert pessoa is not None
        republicas = pessoa.morador_em_republicas
        assert len(republicas) == 1
        assert urlparse(response.response.location).path == url(controller='republica', action='show', id=republicas[0].id)


    def test_ativacao_cadastro_mas_sem_criar_republica(self):
        '''
        Pessoa fornece dados completos
        '''
        email = 'abc@xyz.com'
        cp = CadastroPendente(email=email)
        Session.commit()
        link = cp.link_confirmacao
        
        response = self.app.post(url=link,
                                params={
                                        'nome': 'Teste ABC',
                                        'senha': '1234',
                                        'confirmacao_senha': '5678',
                                        'aceito_termos': '1',
                                        'criar_nova_republica': '0',
                                        }
                                )
        
        # assert user.email = email do cadastro pendente
        assert CadastroPendente(email=email) is None
        pessoa = Pessoa.get_by(email=email)
        assert pessoa is not None
        republicas = pessoa.morador_em_republicas
        assert len(republicas) == 0
        assert urlparse(response.response.location).path == url(controller='pessoa', action='edit', id=pessoa.id)
        
    
    def test_ativacao_cadastro_mas_pessoa_ja_tem_convite_morador(self):
        '''
        Pessoa tenta se cadastrar, mas já tem convite para ser morador em uma república.
        Deve ser redirecionado para outra página
        '''
        mes_passado = date.today() - timedelta(days=30)
        p = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        republica = Republica(nome='Mae Joana', 
                        data_criacao = mes_passado,
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        Morador(pessoa=p, republica=republica, entrada=date.today())
        email_convidado = 'fulano@xyz.com'
        ConviteMorador(email=email_convidado, republica=republica, user=p)
        cp = CadastroPendente(email=email_convidado)
        Session.commit()
        link = cp.link_confirmacao
        
        response = self.app.get(url=link)
        
        assert urlparse(response.response.location).path == url(controller='confirmacao', action='convite_morador', id=cp.hash)
        
