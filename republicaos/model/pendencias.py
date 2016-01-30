# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from elixir      import Unicode, Boolean, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, using_options, using_table_options, using_mapper_options
from elixir      import Field, OneToMany, ManyToOne
from sqlalchemy  import types, and_, or_, select, UniqueConstraint, func

from elixir.events import before_insert, after_insert, after_update
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from republicaos.model import Session, Pessoa
from republicaos.lib.mail import send_email
from republicaos.lib.utils import encrypt

from pylons import config

from paste.request import construct_url
from itertools import izip

from pylons import request, response, tmpl_context as c
from republicaos.lib.helpers import url, flash

import logging

log = logging.getLogger(__name__)

dias_expiracao = 7


class CadastroPendente(Entity):
    using_options(tablename = 'cadastro_pendente')

    hash = Field(String(40), primary_key = True)
    email = Field(String(80), required=True, unique=True)
    data_pedido = Field(DateTime, required=True, default=datetime.now)

    #TODO: ver como fica a tradução com o Babel
    subject = 'Republicaos: verificação de endereço de e-mail'
    mensagem_confirmacao = '''
Oi,

Recebemos sua soliticação de cadastro no Republicaos. Para completar o processo, é necessário que você confirme o recebimento desta mensagem de ativação. Para isto, basta clicar no link abaixo:

%(link)s

Após a ativação, você poderá utilizar as funcionalidades do Republicaos, criando uma república e convidando outros moradores da república para participar.

Caso não tenha interesse em confirmar o cadastro, nenhuma ação é necessária. Esse pedido expirará automaticamente em alguns dias.

Atenciosamente,

--
Equipe Republicaos'''

    @before_insert
    def _set_hash(self):
        self.hash = encrypt(self.email)


    @property
    def link_confirmacao(self):
        action = 'ativacao_nova_conta'
        try:
            url_ = construct_url(request.environ, script_name = url(controller='confirmacao',
                            action=action, id=self.hash), with_path_info=False)
        except TypeError:
            # fora de uma chamada a uma requisição, request não fica registrado
            # acontece em alguns casos de teste
            url_ = url(controller='confirmacao', action=action, id=self.hash)
        return url_


    @after_insert
    @after_update
    def enviar_pedido_confirmacao(self):
        mensagem = self.mensagem_confirmacao % {'link':self.link_confirmacao}
        log.debug('CADASTRO_PENDENTE: enviar_pedido_confirmacao: %s' % mensagem)
        send_email(to_address=self.email, message=mensagem, subject=self.subject)
        try:
            flash('Uma mensagem de ativação do cadastro foi enviada para o e-mail fornecido.', 'info')
        except TypeError:
            # exceção esperada em um caso de teste fora de uma request
            pass
        return


class TrocaSenha(Entity):
    hash = Field(String(40), primary_key = True)
    pessoa = ManyToOne('Pessoa', required=True)
    data_pedido = Field(DateTime, default = datetime.now)
    
    subject = 'Republicaos: Alteração de senha'
    mensagem_recadastro = '''
Oi %(nome)s,

Recebemos um pedido para recadastro da sua senha no Republicaos. Para isto, basta clicar no link abaixo:

%(link)s

Caso não tenha interesse em recadastrar uma nova senha, nenhuma ação é necessária. Esse pedido expirará automaticamente em alguns dias.

Atenciosamente,

--
Equipe Republicaos'''


    @before_insert
    def _set_hash(self):
        self.hash = encrypt(self.pessoa.nome, self.pessoa.email)

    @property
    def link_confirmacao(self):
        try:
            url_ = construct_url(request.environ, script_name = url(controller='confirmacao',
                            action='troca_senha', id=self.hash), with_path_info=False)
        except TypeError:
            # fora de uma chamada a uma requisição, request não fica registrado
            # acontece em alguns casos de teste
            url_ = url(controller='confirmacao', action='troca_senha', id=self.hash)
        return url_

    @after_insert
    @after_update
    def enviar_mensagem(self):
        mensagem = self.mensagem_recadastro % {'nome':self.pessoa.nome, 'link':self.link_confirmacao}
        send_email(to_address=self.pessoa.email, message=mensagem, subject=self.subject)
        try:
            flash('Um link para a página da troca de senha foi enviada para seu e-mail', 'info')
        except TypeError:
            # exceção esperada em um caso de teste fora de uma request
            pass
        return

class ConviteMorador(Entity):
    using_options(tablename = 'convite_morador')

    hash = Field(String(40), primary_key = True)
    email = Field(String(80), required=True)
    entrada = Field(Date, default=date.today())
    data_pedido = Field(DateTime, required=True, default=datetime.now)
    user = ManyToOne('Pessoa', required=True)
    republica = ManyToOne('Republica', required=True)
    
    # restrição abaixo não seria mais necessária já que o hash vai ser
    # calculado só com o e-mail, garantindo no máx um convite por e-mail
    using_table_options(UniqueConstraint('email', 'republica_id'))
    
    subject = 'Republicaos: Convite de %(anfitriao)s para ingressar na república %(republica)s'
    mensagem = '''
Oi,

%(anfitriao)s está lhe convidando para ingressar como morador na república %(republica)s. Para isto, basta clicar no link abaixo:

%(link)s

Caso não tenha interesse em participar, nenhuma ação é necessária. Esse pedido expirará automaticamente em alguns dias.

Atenciosamente,

--
Equipe Republicaos'''


    @before_insert
    def _confirma_nome_pessoa(self):
        pessoa = Pessoa.get_by(email=self.email)
        if pessoa: # o convidado já é morador
            # usar o nome cadastrado no sistema
            self.nome = pessoa.nome


    @before_insert
    def _set_hash(self):
        self.hash = encrypt(self.email)

    @property
    def link_confirmacao(self):
        action = 'convite_morador'
        try:
            url_ = construct_url(request.environ, script_name = url(controller='confirmacao',
                            action=action, id=self.hash), with_path_info=False)
        except TypeError:
            # fora de uma chamada a uma requisição, request não fica registrado
            # acontece em alguns casos de teste
            url_ = url(controller='confirmacao', action=action, id=self.hash)
        return url_

    @after_insert
    def enviar_mensagem(self):
        assunto = self.subject % {'anfitriao':self.user.nome, 'republica':self.republica.nome}
        mensagem = self.mensagem % {
                #'nome':self.nome,
                'anfitriao':self.user.nome or self.user.email,
                'republica':self.republica.nome,
                'link':self.link_confirmacao
            }
        send_email(to_address=self.email, message=mensagem, subject=assunto)
        try:
            flash('Um link com o convite foi enviado para o(s) e-mail(s) informado(s)', 'info')
        except TypeError:
            # exceção esperada em um caso de teste fora de uma request
            pass
        return
    
    
    @classmethod
    def convidar_moradores(cls, emails, user, republica, entrada):
        if isinstance(emails, basestring):
            emails=[emails]

        for email in emails:
            pessoa = Pessoa.get_by(email=email)
            if pessoa and republica in pessoa.morador_em_republicas:
                try:
                    flash('%s não foi convidado(a) pois já é morador(a) da república', 'warning')
                except TypeError:
                    # exceção esperada em um caso de teste fora de uma request
                    log.debug('(warning) %s não foi convidado(a) pois já é morador(a) da república')
                    pass
                    
                continue
            convite = ConviteMorador.get_by(email=email, republica=republica)
            if not convite:
                convite = ConviteMorador(email=email, user=user, republica=republica, entrada=entrada)
                Session.commit()
            else:
                convite.enviar_mensagem()
        return

