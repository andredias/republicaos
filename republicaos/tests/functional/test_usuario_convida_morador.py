# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, ConviteMorador, Fechamento, Session
from republicaos.lib.helpers import flash, url
from datetime import date, datetime, timedelta
from urlparse import urlparse
from babel.dates import format_date

import logging
log = logging.getLogger(__name__)

class TestUsuarioConvidaMorador(TestController):
    def test_usuario_anonimo_tenta_acessar(self):
        ontem = date.today() - timedelta(days=1)
        ano_passado = date.today() - timedelta(days=365)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        republica = Republica(nome='Mae Joana', 
                        data_criacao = ano_passado,
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        republica2 = Republica(nome='Jeronimo', 
                        data_criacao = ano_passado,
                        endereco = 'R. Jeronimo Pattaro, 186, Campinas, SP',
                        latitude = 0,
                        longitude = 0)

        Fechamento(data=ano_passado + timedelta(days=30), republica=republica)
        Fechamento(data=ano_passado + timedelta(days=30), republica=republica2)

        Fechamento(data=date.today() - timedelta(days=30), republica=republica)
        Fechamento(data=date.today() - timedelta(days=30), republica=republica2)
        
        Fechamento(data=date.today() + timedelta(days=30), republica=republica)
        Fechamento(data=date.today() + timedelta(days=30), republica=republica2)
        
        Morador(pessoa=p1, republica=republica, entrada=date.today())
        Morador(pessoa=p2, republica=republica, entrada=ano_passado, saida=ano_passado + timedelta(days=10))
        Morador(pessoa=p2, republica=republica2, entrada=ontem)
        Session.commit()
        
        # depois que Session para de valer, n??o d?? para acessar novamente seus atributos
        inicio_intervalo, fim_intervalo = republica.fechamento_atual.intervalo
        
        p1 = p1.to_dict()
        p2 = p2.to_dict()

        republica = republica.to_dict()
        republica2 = republica2.to_dict()
        
        # acesso sem especificar a rep??blica
        response = self.app.post(
                        url=url(controller='morador', action='new'),
                        status=404
                    )
                
        url_ = url(controller='morador', action='new', republica_id=republica['id'])
        
        # acesso de usu??rio an??nimo
        response = self.app.post(url=url_, status=302)
        assert ConviteMorador.get_by() is None
        
        # convite com data de entrada < ??ltimo_fechamento
        email = 'siclano@republicaos.com.br'
        response = self.app.post(
                        url=url_,
                        params={
                            'nome':'Siclano',
                            'email':email,
                            'entrada': format_date(inicio_intervalo - timedelta(days=1))
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        
        assert 'erro_entrada' in response
        assert str(response).count('class="error-message"') == 1

        # convite com data de entrada >= pr??ximo_fechamento
        email = 'siclano@republicaos.com.br'
        response = self.app.post(
                        url=url_,
                        params={
                            'nome':'Siclano',
                            'email':email,
                            'entrada': format_date(fim_intervalo + timedelta(days=1))
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        
        assert 'erro_entrada' in response
        assert str(response).count('class="error-message"') == 1



        # convite ok
        email = 'siclano@republicaos.com.br'
        assert ConviteMorador.get_by(email=email) == None
        response = self.app.post(
                        url=url_,
                        params={
                            'nome':'Siclano',
                            'email':email,
                            'entrada': format_date(inicio_intervalo)
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        
        assert ConviteMorador.get_by(email=email)
        assert 'link com o convite' in response.session['flash'][-1][1]
        
        # convite ok para morar na outra rep??blica
        
        email = 'siclano@republicaos.com.br'
        response = self.app.post(
                        url=url(controller='morador', action='new', republica_id=republica2['id']),
                        params={
                            'nome':'Siclano',
                            'email':email,
                            'entrada': format_date(inicio_intervalo)
                            },
                        extra_environ={str('REMOTE_USER'):str('2')}
                    )
        
        assert ConviteMorador.get_by(email=email, republica_id=republica2['id'])
        assert 'link com o convite' in response.session['flash'][-1][1]
        
        # convite a um ex-morador | pessoa j?? cadastrada
        response = self.app.post(
                        url=url_,
                        params={
                            'nome':'Beltranix da Silva',
                            'email':p2['email'],
                            'entrada': format_date(inicio_intervalo)
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        
        convite = ConviteMorador.get_by(email=p2['email'])
        assert convite.nome == 'Beltrano'
        assert 'link com o convite' in response.session['flash'][-1][1]
        
        # convite a uma pessoa que j?? ?? moradora
        response = self.app.post(
                        url=url_,
                        params={
                            'nome':'Fulanix de Tal',
                            'email':p1['email'],
                            'entrada': format_date(inicio_intervalo)
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        
        assert ConviteMorador.get_by(email=p1['email']) is None
        assert 'n??o foi convidado(a) pois j?? ?? morador(a)' in response.session['flash'][-1][1]
        
