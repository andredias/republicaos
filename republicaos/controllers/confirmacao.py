# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.lib.validators import DataNoFechamento
from republicaos.lib import auth as authentication
from republicaos.model import CadastroPendente, TrocaSenha, Pessoa, Session, ConviteMorador, Morador
from formencode import Schema, validators
from datetime import date, timedelta

log = logging.getLogger(__name__)

def get_republica_from_convite_morador():
    c.convite = ConviteMorador.get_by(hash=request.urlvars['id'])
    return c.convite.republica if c.convite else None

class ConviteMoradorSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True, strip=True)
#    email = formencode.All(validators.Email(not_empty=True), Unique(model=Pessoa, attr='email'))
    senha = validators.UnicodeString(not_empty=True, min=4)
    confirmacao_senha = validators.UnicodeString()
    chained_validators = [validators.FieldsMatch('senha', 'confirmacao_senha')]
    aceito_termos = validators.NotEmpty(messages={'empty': 'Aceite os termos de uso'})
    entrada = DataNoFechamento(not_empty=True, get_republica=get_republica_from_convite_morador)


class ConviteMoradorSchema2(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    entrada = DataNoFechamento(not_empty=True, get_republica=get_republica_from_convite_morador)


def check_convidado_is_user():
    hash = request.urlvars.get('id')
    log.debug('check_convidado_is_user: hash: %s', hash)
    convite = ConviteMorador.get_by(hash=hash)
    if not convite:
        return False
    user = Pessoa.get_by(email=convite.email)
    return user


class ConfirmacaoController(BaseController):
    def cadastro(self, id):
        cp = CadastroPendente.get_by(hash = id)
        if cp:
            user = cp.confirma_cadastro()
            authentication.set_user(user)
            flash('(info) Bem vindo ao Republicaos, %s!' % cp.nome)
            redirect_to(controller='root', action='index')
        else:
            return render('confirmacao/confirmacao_invalida.html')



    @validate(ConviteMoradorSchema, alternative_schema=ConviteMoradorSchema2, check_function=check_convidado_is_user)
    def convite_morador(self, id):
        c.convite = ConviteMorador.get_by(hash=id)
        if not c.convite:
            return render('confirmacao/confirmacao_invalida.html')

        user = Pessoa.get_by(email=c.convite.email)
        authentication.set_user(user)
        if c.valid_data:
            # cadastrar pessoa
            if not user:
                user = Pessoa(
                                nome=c.valid_data['nome'],
                                senha=c.valid_data['senha'],
                                email=c.convite.email
                            )
            Morador(pessoa=user, republica=c.convite.republica, entrada=c.valid_data['entrada'])
            flash('(info) Bem vindo(a) à república %s!' % c.convite.republica.nome)
            destino = url_for(controller='republica', action='show', republica_id=c.convite.republica.id)
            c.convite.delete()
            Session.commit()
            authentication.set_user(user)
            redirect_to(destino)
        # FIXME: problemas com unicode
        c.title = 'Confirmacao do convite para participar da republica %s' % c.convite.republica.nome
        c.action = url_for(controller='confirmacao', action='convite_morador', id=id)
        filler_data = request.params or c.convite.to_dict()
        if isinstance(filler_data.get('entrada'), date):
            filler_data['entrada'] = filler_data['entrada'].strftime('%d/%m/%Y')
        return render('confirmacao/convite_morador.html', filler_data=filler_data)



    def troca_senha(self, id):
        ts = TrocaSenha.get_by(hash=id)
        if ts:
            authentication.set_user(ts.pessoa)
            flash('(info) Entre com a nova senha')
            ts.delete()
            Session.commit()
            redirect_to(controller='pessoa', action='edit', id=ts.pessoa.id)
        else:
            return render('confirmacao/confirmacao_invalida.html')
