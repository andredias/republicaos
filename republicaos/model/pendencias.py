# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from elixir      import Unicode, Boolean, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, using_options, using_table_options, using_mapper_options
from elixir      import Field, OneToMany, ManyToOne
from datetime    import date, datetime, time
import elixir
from elixir.events import before_insert, after_insert, after_update
from dateutil.relativedelta import relativedelta
from republicaos.model import Session, Pessoa
from republicaos.lib.mail import send_email
from hashlib import sha1
from pylons import config
from paste.request import construct_url

from pylons import request, response, tmpl_context as c
from republicaos.lib.helpers import get_object_or_404, url_for, flash

import logging

log = logging.getLogger(__name__)

dias_expiracao = 7

def hash_calc(*args):
    palavra = ''.join(args).join(config['beaker.session.secret'])
    return sha1(palavra.encode('utf-8')).hexdigest()

class CadastroPendente(Entity):
    using_options(tablename = 'cadastro_pendente')

    hash = Field(String(40), primary_key = True)
    nome =  Field(Unicode(30), required=True)
    _senha = Field(String(40), required=True)
    email = Field(String(80), required=True, unique=True)
    data_pedido = Field(Date, required=True, default=date.today)

    #TODO: ver como fica a tradução com o Babel
    subject = 'Republicaos: verificação de endereço de e-mail'
    mensagem_confirmacao = '''
Oi %(nome)s,

Recebemos sua soliticação de cadastro no Republicaos. Para completar o processo, é necessário que você confirme o recebimento desta mensagem de ativação. Para isto, basta clicar no link abaixo:

%(link)s

Após a ativação, você poderá utilizar as funcionalidades do Republicaos, criando uma república e convidando outros moradores da república para participar.

Caso não tenha interesse em confirmar o cadastro, nenhuma ação é necessária. Esse pedido expirará automaticamente em alguns dias.

Atenciosamente,

--
Equipe Republicaos'''

    def _set_senha(self, password):
        self._senha = sha1(password).hexdigest()

    def _get_senha(self):
        return self._senha

    senha = property(_get_senha, _set_senha)

    @before_insert
    def _set_hash(self):
        self.hash = hash_calc(self.nome, self.senha, self.email)


    def confirma_cadastro(self):
        pessoa = Pessoa(nome=self.nome, _senha=self._senha, email=self.email, data_cadastro = date.today())
        self.delete()
        Session.commit()
        return pessoa

    @property
    def link_confirmacao(self):
        try:
            url = construct_url(request.environ, script_name = url_for(controller='confirmacao',
                            action='cadastro', id=self.hash), with_path_info=False)
        except TypeError:
            # fora de uma chamada a uma requisição, request não fica registrado
            # acontece em alguns casos de teste
            url = url_for(controller='confirmacao', action='cadastro', id=self.hash)
        return url


    @after_insert
    @after_update
    def enviar_pedido_confirmacao(self):
        mensagem = self.mensagem_confirmacao % {'nome':self.nome, 'link':self.link_confirmacao}
        log.debug('CADASTRO_PENDENTE: enviar_pedido_confirmacao: %s' % mensagem)
        send_email(to_address=self.email, message=mensagem, subject=self.subject)
        try:
            flash('(info) Uma mensagem de ativação do cadastro foi enviada para o e-mail fornecido.')
        except TypeError:
            # exceção esperada em um caso de teste fora de uma request
            pass
        return


class TrocaSenha(Entity):
    hash = Field(String(40), primary_key = True)
    pessoa = ManyToOne('Pessoa', required=True)
    data_pedido = Field(Date, default = date.today)
    
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
        self.hash = hash_calc(self.pessoa.nome, self.pessoa.email)

    @property
    def link_confirmacao(self):
        try:
            url = construct_url(request.environ, script_name = url_for(controller='confirmacao',
                            action='troca_senha', id=self.hash), with_path_info=False)
        except TypeError:
            # fora de uma chamada a uma requisição, request não fica registrado
            # acontece em alguns casos de teste
            url = url_for(controller='confirmacao', action='troca_senha', id=self.hash)
        return url

    @after_insert
    @after_update
    def enviar_mensagem(self):
        mensagem = self.mensagem_recadastro % {'nome':self.pessoa.nome, 'link':self.link_confirmacao}
        send_email(to_address=self.pessoa.email, message=mensagem, subject=self.subject)
        try:
            flash('(info) Um link para a página da troca de senha foi enviada para seu e-mail')
        except TypeError:
            # exceção esperada em um caso de teste fora de uma request
            pass
        return

