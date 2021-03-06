# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, TipoDespesa, Fechamento, Session
from republicaos.lib.helpers import flash, url
from republicaos.lib.utils import testing_app
from urlparse import urlparse
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


import logging
log = logging.getLogger(__name__)


class TestAutenticacaoAutorizacao(TestController):
    def test_login_dados_incompletos(self):
        '''
        Dados incompletos no formulário de login
        '''
        response = self.app.post(
                        url=url(controller='root', action='login'),
                        params={
                                'email':'xyz@abc.com.br',
                                }
                        )
        log.debug('response: %s', response)
        assert 'erro_senha' in response.body
    
    
    def test_login_email_inexistente(self):
        '''
        Tenta fazer login com e-mail inexistente
        '''
        response = self.app.post(
                        url=url(controller='root', action='login'),
                        params={
                                'email':'xyz@abc.com.br',
                                'senha':'1234'
                                }
                        )
        assert 'class="avisos_panel"' in response
        assert 'O e-mail e/ou a senha fornecidos não conferem' in response
        
    
    def test_login_senha_incorreta(self):
        '''
        Tenta fazer login com e-mail correto, mas senha incorreta
        '''
        Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        Session.commit()
        response = self.app.post(
                        url=url(controller='root', action='login'),
                        params={
                                'email':'abc@xyz.com.br',
                                'senha':'12345'
                                }
                        )
        
        assert 'O e-mail e/ou a senha fornecidos não conferem' in response
    
    
    def test_login_correto_correto_sem_redirecionamento(self):
        '''
        Dados corretos, redirecionando para página inicial
        '''
        email = 'abc@xyz.com.br'
        senha = '1234'
        pessoa = Pessoa(nome='Fulano', email=email, senha=senha)
        Session.commit()
        response = self.app.post(
                        url=url(controller='root', action='login'),
                        params={
                                'email':email,
                                'senha':senha
                                }
                        )
        assert response.session['userid'] == pessoa.id
        assert urlparse(response.response.location).path == url(controller='pessoa', action='painel', id=pessoa.id)
    
    
    def test_login_correto_com_redirecionamento(self, came_from = None):
        '''
        Dados corretos, mas redirecionando para uma página que supostamente exigiu login
        '''
        email = 'abc@xyz.com.br'
        senha = '1234'
        user = Pessoa(nome='Fulano', email=email, senha=senha)
        Session.commit()
        
        if not came_from:
            came_from = url(controller='test', action='requer_login')
        response = self.app.get(url = came_from, status=302)
        log.debug('response.session: %s', response.session)
        assert response.session['came_from'] == came_from
        assert urlparse(response.response.location).path == url(controller='root', action='login')
        
        # não consegui fazer o response = response.follow funcionar
        response = self.app.post(
                        url=url(controller='root', action='login'),
                        params={
                                'email':email,
                                'senha':senha
                                },
                        status = 302
                        )
        # precisa pegar o usuário de novo
        user = Pessoa.get_by()
        assert urlparse(response.response.location).path == came_from
        assert response.session.get('came_from') is None
        assert response.session['userid'] == user.id
        
        
    def test_owner_required_dono_correto(self):
        '''
        Recurso exige que o usuário seja o dono do recurso para acessá-lo
        '''
        destino = url(controller='test', action='requer_owner', id='1')
        self.test_login_correto_com_redirecionamento(destino)
        response = self.app.get(url=destino)
        
        
    def test_owner_required_dono_incorreto(self):
        '''
        Usuário incorreto tenta acessar recurso
        '''
        destino = url(controller='test', action='requer_owner', id='1000')
        self.test_login_correto_com_redirecionamento(destino)
        response = self.app.get(url=destino, status=403)
        
    
    def _cadastra_massa_testes(self):
        ontem = date.today() - timedelta(days=1)
        ano_passado = date.today() - timedelta(days=365)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        republica = Republica(nome='Mae Joana', 
                        data_criacao = ano_passado,
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Morador(
            pessoa=p2,
            republica=republica,
            entrada=ano_passado, 
            saida=ano_passado + relativedelta(months=2)
            )
        TipoDespesa(nome='luz', republica=republica)
        Fechamento(data=date.today() - relativedelta(months=1), republica=republica)
        Fechamento(data=date.today(), republica=republica)
        Fechamento(data=date.today() + relativedelta(months=1), republica=republica)
        Session.commit()
        
        p3 = Pessoa(nome='Siclano', email='siclano@republicaos.com.br', senha='1234')
        republica2 = Republica(nome='Jeronimo', 
                        data_criacao = ontem,
                        endereco = 'R. Jeronimo Pattaro, 186 - Campinas -SP',
                        latitude = 0,
                        longitude = 0)
        Morador(pessoa=p3, republica=republica2, entrada=ontem)
        Session.commit()
        
    
    
    def test_requer_morador(self):
        '''
        É necessário um usuário autenticado que seja morador para acessar este
        recurso
        '''
        self._cadastra_massa_testes()
        destino = url(
                          controller='test',
                          action='requer_morador',
                          republica_id='1',
                          id='1'
                        )
        response = self.app.get(url=destino, status=302) # anônimo
        assert urlparse(response.response.location).path == url(controller='root', action='login')
        assert response.session['came_from'] == destino
        
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('1')}) # morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('2')}, status=403) # ex-morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('3')}, status=403) # não-morador

        # tenta acessar recurso sem especificar a república
        destino = url(
                          controller='test',
                          action='requer_morador',
                          id='1'
                        )
        response = self.app.get(url=destino, status=404) # anônimo
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('1')}, status=404) # morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('2')}, status=404) # ex-morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('3')}, status=404) # não-morador
    
    
    def test_requer_morador_ou_ex(self):
        '''
        É necessário um usuário autenticado que seja morador ou ex-morador para acessar este
        recurso
        '''
        self._cadastra_massa_testes()
        destino = url(
                          controller='test',
                          action='requer_morador_ou_ex',
                          republica_id='1',
                          id='1'
                        )
        response = self.app.get(url=destino, status=302) # anônimo
        assert urlparse(response.response.location).path == url(controller='root', action='login')
        assert response.session['came_from'] == destino
        
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('1')}) # morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('2')}) # ex-morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('3')}, status=403) # não-morador
        
        # tenta acessar recurso sem especificar a república
        destino = url(
                          controller='test',
                          action='requer_morador_ou_ex',
                          id='1'
                        )
        response = self.app.get(url=destino, status=404) # anônimo
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('1')}, status=404) # morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('2')}, status=404) # ex-morador
        response = self.app.get(url=destino, extra_environ={str('REMOTE_USER'):str('3')}, status=404) # não-morador


    def test_requer_republica(self):
        '''
        Só acessa o recurso se houver republica_id na URL
        '''
        self._cadastra_massa_testes()

        #ok
        response = self.app.get(
                        url=url(
                          controller='test',
                          action='requer_republica',
                          republica_id='1',
                          id='1'
                        )
                    )
 
        # acessa url sem republica_id
        response = self.app.get(
                        url=url(
                          controller='test',
                          action='requer_republica',
                          id='1'
                        ),
                        status=404
                    )
        
        # republica inexistente
        response = self.app.get(
                        url=url(
                          controller='test',
                          action='requer_republica',
                          republica_id='1000',
                          id='1'
                        ),
                        status=404
                    )
    
    
    def test_requer_recurso_republica(self):
        '''
        O recurso sendo acessado tem de ser da república sendo acessada.
        Também é necessário que seja acessado por um morador.
        '''
        
        self._cadastra_massa_testes()
        
        # ok
        response = self.app.get(
                        url=url(
                                controller='test',
                                action='requer_recurso_republica',
                                republica_id=1,
                                id='1'
                        ),
                        extra_environ={str('REMOTE_USER'):str('1')},
                    )
        
        # tenta acesso anônimo
        response = self.app.get(
                        url=url(
                                controller='test',
                                action='requer_recurso_republica',
                                republica_id=1,
                                id='1'
                        ),
                        status=302
                    )
        
        # ex-morador tenta acesso
        response = self.app.get(
                        url=url(
                                controller='test',
                                action='requer_recurso_republica',
                                republica_id=1,
                                id='1'
                        ),
                        extra_environ={str('REMOTE_USER'):str('2')},
                        status=403
                    )
        
        # acesso sem especificar a república
        response = self.app.get(
                        url=url(
                                controller='test',
                                action='requer_recurso_republica',
                                id='1'
                        ),
                        extra_environ={str('REMOTE_USER'):str('1')},
                        status=404
                    )
