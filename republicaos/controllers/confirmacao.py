# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.lib import auth as authentication
from republicaos.model import CadastroPendente, Pessoa, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class ConfirmacaoController(BaseController):
    def cadastro(self, id):
        cp = CadastroPendente.get_by(hash = id)
        if cp:
            pessoa = Pessoa(nome=cp.nome, _senha=cp._senha, email=cp.email)
            authentication.set_user(pessoa.email)
            flash('(info) Bem vindo ao Republicaos, %s!' % pessoa.nome)
            cp.delete()
            Session.commit()
            redirect_to(controller='root', action='index')
        else:
            return render('confirmacao/confirmacao_invalida.html')


    def convite(self, id):
        pass
