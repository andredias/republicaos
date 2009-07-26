# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from elixir      import Unicode, Boolean, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, using_options, using_table_options, using_mapper_options
from elixir      import Field, OneToMany, ManyToOne
from datetime    import date, datetime, time
import elixir
from elixir.events import before_insert
from dateutil.relativedelta import relativedelta
from republicaos.model import Session, Pessoa
from republicaos.lib.mail import send_email
from hashlib import sha1
from pylons import config
import logging

log = logging.getLogger(__name__)

dias_expiracao = 7

class CadastroPendente(Entity):
    using_options(tablename = 'cadastro_pendente')

    hash = Field(String(40), primary_key = True)
    nome =  Field(Unicode(30), required=True)
    _senha = Field(String(40), required=True)
    email = Field(String(80), required=True, unique=True)
    data_pedido = Field(Date, required=True, default=date.today())

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
        palavra = ''.join([self.nome, self.senha, self.email, config['beaker.session.secret']])
        self.hash = sha1(palavra.encode('utf-8')).hexdigest()


    def confirma_cadastro(self):
        p = Pessoa(nome=self.nome, _senha=self._senha, email=self.email, data_cadastro = date.today())
        self.delete()
        Session.commit()

    def enviar_pedido_confirmacao(self, link):
        mensagem = self.mensagem_confirmacao % {'nome':self.nome, 'link':link}
        log.debug('CADASTRO_PENDENTE: enviar_pedido_confirmacao: %s' % mensagem)
        send_email(to_address=self.email, message=mensagem, subject=self.subject)
        return

