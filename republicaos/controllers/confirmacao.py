# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from republicaos.lib.helpers import get_object_or_404, url, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.lib.validators import Date
from republicaos.lib.auth import set_user, get_user
from republicaos.model import CadastroPendente, TrocaSenha, Pessoa, Session
from republicaos.model import ConviteMorador, Morador
from formencode import Schema, validators
from datetime import date, timedelta

log = logging.getLogger(__name__)


def get_republica_from_convite_morador():
    c.convite = ConviteMorador.get_by(hash=request.urlvars['id'])
    log.debug('c.convite: %s', c.convite)
    return c.convite.republica if c.convite else None


class CadastroSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True, strip=True)
    senha = validators.UnicodeString(not_empty=True, min=4)
    confirmacao_senha = validators.UnicodeString()
    aceito_termos = validators.NotEmpty(messages={'empty': 'Aceite os termos de uso'})
    chained_validators = [validators.FieldsMatch('senha', 'confirmacao_senha')]


class ConviteMoradorSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True, strip=True)
#    email = formencode.All(validators.Email(not_empty=True), Unique(model=Pessoa, attr='email'))
    senha = validators.UnicodeString(not_empty=True, min=4)
    confirmacao_senha = validators.UnicodeString()
    chained_validators = [validators.FieldsMatch('senha', 'confirmacao_senha')]
    aceito_termos = validators.NotEmpty(messages={'empty': 'Aceite os termos de uso'})
    entrada = Date(
                    not_empty=True,
                    min=lambda: get_republica_from_convite_morador().intervalo_valido_lancamento[0],
                    max=lambda: get_republica_from_convite_morador().intervalo_valido_lancamento[1]
                )


class ConviteMoradorSchema2(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    entrada = Date(
                    not_empty=True,
                    min=lambda: get_republica_from_convite_morador().intervalo_valido_lancamento[0],
                    max=lambda: get_republica_from_convite_morador().intervalo_valido_lancamento[1]
                )


def check_convidado_is_user():
    hash = request.urlvars.get('id')
    log.debug('check_convidado_is_user: hash: %s', hash)
    convite = ConviteMorador.get_by(hash=hash)
    if not convite:
        return False
    user = Pessoa.get_by(email=convite.email)
    return user


class ConfirmacaoController(BaseController):
    
    @validate(CadastroSchema)
    def ativacao_nova_conta(self, id):
        if ConviteMorador.get_by(hash=id):
            # j?? possui convite para ser morador
            redirect(url(controller='confirmacao', action='convite_morador', id=id))
        cp = CadastroPendente.get_by(hash=id)
        if not cp:
            flash('O link fornecido para confirma????o de email n??o ?? v??lido. Por favor, refa??a o pedido de nova conta.', 'error')
            redirect(url(controller='pessoa', action='pedido_nova_conta'))
        elif c.valid_data:
            pessoa = Pessoa(email=cp.email, nome=c.valid_data['nome'], senha=c.valid_data['senha'])
            set_user(pessoa)
            # cadastrar rep??blica
            # convidar moradores
            cp.delete()
            Session.commit()
            flash('Bem vindo ao Republicaos, %s!' % pessoa.nome, 'info')
            redirect(url(controller='pessoa', action='painel', id=user.id))
        elif c.errors:
            flash('O formul??rio n??o foi preenchido corretamente', 'error')
        return render('confirmacao/ativacao_nova_conta.html', filler_data=request.params)


    @validate(ConviteMoradorSchema, alternative_schema=ConviteMoradorSchema2,
              check_function=check_convidado_is_user)
    def convite_morador(self, id):
        c.convite = ConviteMorador.get_by(hash=id)
        if not c.convite:
            flash('O link fornecido para confirma????o do convite para ser morador da rep??blica n??o ?? v??lido. Por favor, entre em contato com a pessoa que lhe indicou para que ela fa??a um novo convite.', 'error')
            c.action = 'login'
            return render('root/login_nova_conta_esqueci_senha.html')

        set_user(Pessoa.get_by(email=c.convite.email))
        c.user = get_user()
        if c.valid_data:
            # cadastrar pessoa
            if not c.user:
                c.user = Pessoa(
                                nome=c.valid_data['nome'],
                                senha=c.valid_data['senha'],
                                email=c.convite.email
                            )
            Morador(pessoa=c.user, republica=c.convite.republica, entrada=c.valid_data['entrada'])
            flash('Bem vindo(a) ?? rep??blica %s!' % c.convite.republica.nome, 'info')
            destino = url(controller='republica', action='show', republica_id=c.convite.republica.id)
            c.convite.delete()
            Session.commit()
            set_user(c.user)
            redirect(destino)
        # FIXME: problemas com unicode
        c.title = 'Confirmacao do convite para participar da republica %s' % c.convite.republica.nome
        c.action = url(controller='confirmacao', action='convite_morador', id=id)
        filler_data = request.params or c.convite.to_dict()
        if isinstance(filler_data.get('entrada'), date):
            filler_data['entrada'] = filler_data['entrada'].strftime('%d/%m/%Y')
        return render('confirmacao/convite_morador.html', filler_data=filler_data)


    def troca_senha(self, id):
        ts = TrocaSenha.get_by(hash=id)
        if ts:
            set_user(ts.pessoa)
            flash('Entre com a nova senha', 'info')
            ts.delete()
            Session.commit()
            redirect(url(controller='pessoa', action='edit', id=ts.pessoa.id))
        else:
            flash('O link fornecido para troca de senha n??o ?? v??lido. Por favor, fa??a um novo pedido.', 'error')
            return render('root/login_nova_conta_esqueci_senha.html')
