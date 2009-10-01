# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from republicaos.tests import TestController
from republicaos.model import Pessoa, Republica, Morador, ConviteMorador, Session
from republicaos.model import DespesaAgendada
from sqlalchemy  import and_
from republicaos.lib.helpers import flash, url_for
from datetime import date, datetime, timedelta
from babel.dates import format_date
from urlparse import urlparse

import logging
log = logging.getLogger(__name__)

class TestMoradorSaiDaRepublica(TestController):
    def test_desligamento_republica(self):
        ontem = date.today() - timedelta(days=1)
        mes_passado = date.today() - timedelta(days=30)
        p1 = Pessoa(nome='Fulano', email='abc@xyz.com.br', senha='1234')
        p2 = Pessoa(nome='Beltrano', email='beltrano@republicaos.com.br', senha='1234')
        p3 = Pessoa(nome='Siclano', email='siclano@republicaos.com.br', senha='1234')
        republica = Republica(nome='Mae Joana', 
                        data_criacao = mes_passado,
                        endereco = 'R. dos Bobos, n. 0, Sumare, SP',
                        latitude = 0,
                        longitude = 0)
        Session.commit()
        
        republica2 = Republica(nome='Jeronimo', 
                        data_criacao = mes_passado,
                        endereco = 'R. Jeronimo Pattaro, 186, Campinas, SP',
                        latitude = 0,
                        longitude = 0)
        Morador(pessoa=p1, republica=republica, entrada=mes_passado)
        Morador(pessoa=p2, republica=republica, entrada=mes_passado, saida=ontem)
        Morador(pessoa=p2, republica=republica2, entrada=ontem)
        Morador(pessoa=p3, republica=republica2, entrada=mes_passado)
        
        Session.commit()
        
        DespesaAgendada(
                    pessoa=p1,
                    republica=republica,
                    quantia=100,
                    proximo_lancamento=date.today() + timedelta(days=30),
                    tipo_id='1'
                    )
        DespesaAgendada(
                    pessoa=p1,
                    republica=republica,
                    quantia=123,
                    proximo_lancamento=date.today() + timedelta(days=15),
                    repeticoes=2,
                    tipo_id='2'
                    )
        
        Session.commit()
        
        # depois que Session para de valer, não dá para acessar novamente seus atributos
        p1 = p1.to_dict()
        p2 = p2.to_dict()
        p3 = p3.to_dict()

        republica = republica.to_dict()
        republica2 = republica2.to_dict()
        

        

        # acesso sem especificar a república
        response = self.app.post(
                        url=url_for(controller='morador', action='sair'),
                        status=404,
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )

        url = url_for(controller='morador', action='sair', republica_id=republica['id'])
                    
        # acesso sem especificar o morador
        response = self.app.post(
                        url=url,
                        status=302
                    )
        assert url_for(controller='root', action='login') in response
                    
        # acesso morador de outra república
        response = self.app.post(
                        url=url,
                        status=403,
                        extra_environ={str('REMOTE_USER'):str(p3['id'])}
                    )

        
        # acesso correto
        response = self.app.get(
                        url=url,
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'Registrar desligamento da' in response
        assert 'class="error-message"' not in response
        
        
        # data de saída >= próximo_fechamento
        response = self.app.post(
                        url=url,
                        params={
                            'saida': format_date(date.today() + timedelta(days=100))
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'erro_saida' in response
        
        
        # data de saída < próximo_fechamento
        response = self.app.post(
                        url=url,
                        params={
                            'saida': format_date(mes_passado - timedelta(days=1))
                            },
                        extra_environ={str('REMOTE_USER'):str('1')}
                    )
        assert 'erro_saida' in response
        
        
        # dados corretos
        m = Morador.registro_mais_recente(pessoa=Pessoa.get_by(id=1), republica=Republica.get_by(id=1))
        assert m.saida == None
        response = self.app.post(
                        url=url,
                        params={
                            'saida': format_date(ontem)
                            },
                        extra_environ={str('REMOTE_USER'):str('1')},
                        status = 302
                    )
        assert url_for(controller='root', action='index') in response
        m = Morador.registro_mais_recente(pessoa=Pessoa.get_by(id=1), republica=Republica.get_by(id=1))
        assert m.saida == ontem
        assert DespesaAgendada.query.filter(
                                    and_(
                                        DespesaAgendada.pessoa_id=='1',
                                        DespesaAgendada.republica_id=='1'
                                        )
                                    ).count() == 0
        
        
        # morador tenta sair mais de uma vez
        response = self.app.post(
                        url=url,
                        params={
                            'saida': format_date(date.today())
                            },
                        extra_environ={str('REMOTE_USER'):str('1')},
                        status = 302
                    )
        assert url_for(controller='root', action='index') in response
        m = Morador.registro_mais_recente(pessoa=Pessoa.get_by(id=1), republica=Republica.get_by(id=1))
        assert m.saida == date.today()
        
        
