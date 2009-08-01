# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate
from republicaos.lib.base import BaseController
from formencode import Schema, validators
from republicaos.lib.auth import check_user, get_user, set_user, owner_required


log = logging.getLogger(__name__)

class LoginSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    email = validators.Email(not_empty=True)
    senha = validators.UnicodeString(not_empty=True)

class RootController(BaseController):

    def index(self):
        # veja http://localhost/trac/republicaos_hg/wiki/Evento/PessoaVisitaPaginaInicial
        if c.user: # existe um usuário logado
            # obter lista de repúblicas das quais faz parte
            # obter lista de convites pendentes para morar em república
            pass
        return render('root/index.html')

    @validate(LoginSchema)
    def login(self):
        if c.valid_data:
            user = check_user(c.valid_data['email'], c.valid_data['senha'])
            if user:
                set_user(user)
                destino = session.pop('came_from', url_for(controller='root', action='index'))
                redirect_to(destino)
            else:
                flash('(warning) O e-mail e/ou a senha fornecidos não conferem')
        return render('root/login.html')


    def logout(self):
        set_user(None)
        redirect_to(controller='root', action='index')


