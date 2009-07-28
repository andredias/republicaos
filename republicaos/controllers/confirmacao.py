# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.lib import auth as authentication
from republicaos.model import CadastroPendente, TrocaSenha, Pessoa, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class ConfirmacaoController(BaseController):
    def cadastro(self, id):
        cp = CadastroPendente.get_by(hash = id)
        if cp:
            authentication.set_user(cp.email)
            flash('(info) Bem vindo ao Republicaos, %s!' % cp.nome)
            cp.confirma_cadastro()
            redirect_to(controller='root', action='index')
        else:
            return render('confirmacao/confirmacao_invalida.html')


    def convite(self, id):
        pass
    
    
    def troca_senha(self, id):
        ts = TrocaSenha.get_by(hash=id)
        if ts:
            authentication.set_user(ts.pessoa.email)
            flash('(info) Entre com a nova senha')
            ts.delete()
            Session.commit()
            redirect_to(controller='pessoa', action='edit', id=ts.pessoa.id)
        else:
            return render('confirmacao/confirmacao_invalida.html')
