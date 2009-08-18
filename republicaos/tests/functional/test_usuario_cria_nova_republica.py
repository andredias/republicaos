# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, Session
from republicaos.lib.helpers import flash, url_for
from datetime import date, datetime, timedelta
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestUsuarioCriaRepublica(TestController):
    def test_1(self):
        ontem = date.today() - timedelta(days=1)
        mes_passado = date.today() - timedelta(days=30)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        republica = Republica(nome='Mae Joana', 
                        data_criacao = mes_passado,
                        logradouro = 'R. dos Bobos, n. 0',
                        cidade = 'Sumare',
                        uf = 'SP')
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Session.commit()
        
        # usuário anônimo tenta cadastrar república
        response = self.app.post(url=url_for(controller='republica', action='new'), status=302)
        # o assert abaixo não funciona quando o decorator está no __before__ do controller
        # assert urlparse(response.response.location).path == url_for(controller='root', action='login')
        assert url_for(controller='root', action='login') in response
        
        # usuário autenticado tenta cadastrar república com dados incompletos
        response = self.app.post(
                            url=url_for(controller='republica', action='new'),
                            params={
                                'nome':'Jerônimo',
                                'logradouro':'R. Jerônimo Pattaro, 186',
#                                'complemento':'Barão Geraldo',
#                                'cidade':'Campinas',
                                'uf':'SP',
                            },
                            extra_environ={str('REMOTE_USER'):str('1')}
                        )
        
        # assert urlparse(response.response.location).path == url_for(controller='republica', action='new')
        assert url_for(controller='republica', action='new') in response
        assert 'erro_cidade' in response
        
        # usuário autenticado cadastra república
        response = self.app.post(
                            url=url_for(controller='republica', action='new'),
                            params={
                                'nome':'Jerônimo',
                                'logradouro':'R. Jerônimo Pattaro, 186',
                                'complemento':'Barão Geraldo',
                                'cidade':'Campinas',
                                'uf':'SP',
                            },
                            extra_environ={str('REMOTE_USER'):str('1')}
                        )
        
        assert 'erro' not in response
        p1 = Pessoa.get_by(email='abc@xyz.com.br')
        assert len(p1.morador_em_republicas) == 2
        assert urlparse(response.response.location).path == url_for(
                                                controller='republica', action='show', id='2')

        # usuário p1 tenta cadastrar uma 3a república
        response = self.app.post(
                            url=url_for(controller='republica', action='new'),
                            params={
                                'nome':'Saudade da Mamãe',
                                'logradouro':'Av. da Saudade, 2035',
                                'complemento':'Barão Geraldo',
                                'cidade':'Campinas',
                                'uf':'SP',
                            },
                            extra_environ={str('REMOTE_USER'):str('1')}
                        )
        
        assert 'erro' not in response
        p1 = Pessoa.get_by(email='abc@xyz.com.br')
        assert len(p1.morador_em_republicas) == 2
        assert 'Você já está associado a duas repúblicas' in response
        #assert urlparse(response.response.location).path == url_for(controller='republica', action='new')
        assert url_for(controller='republica', action='new') in response


        # usuário p2 cadastra nova república
        response = self.app.post(
                            url=url_for(controller='republica', action='new'),
                            params={
                                'nome':'Saudade da Mamãe',
                                'logradouro':'Av. da Saudade, 2035',
                                'complemento':'Barão Geraldo',
                                'cidade':'Campinas',
                                'uf':'SP',
                            },
                            extra_environ={str('REMOTE_USER'):str('2')}
                        )
        
        assert 'erro' not in response
        p2 = Pessoa.get_by(email='beltrano@republicaos.com.br')
        assert len(p2.morador_em_republicas) == 1
        assert list(p2.morador_em_republicas)[0].nome == 'Saudade da Mamãe'
        assert urlparse(response.response.location).path == url_for(
                                            controller='republica', action='show', id='3')




