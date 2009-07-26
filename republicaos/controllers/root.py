# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.model import Session
from formencode import Schema, validators

from repoze.what.predicates import not_anonymous
from republicaos.lib.auth import require, get_user


log = logging.getLogger(__name__)

class RootController(BaseController):

    def __before__(self):
        c.user = get_user()
        log.debug('root.__before__: user: %s' % c.user)

    def index(self):
        # veja http://localhost/trac/republicaos_hg/wiki/Evento/PessoaVisitaPaginaInicial
        if c.user: # existe um usuário logado
            # obter lista de repúblicas das quais faz parte
            # obter lista de convites pendentes para morar em república
            pass
        return render('root/index.html')

    def login(self):
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash('(warning) O e-mail e/ou a senha fornecidos não conferem')
        c.login_counter = unicode(login_counter)
        c.came_from = request.params.get('came_from') or url_for(controller='root', action='index')
        return render('root/login.html')

    def post_login(self):
        identity = request.environ.get('repoze.who.identity')
        came_from = request.params.get('came_from') or url_for(controller='root', action='index')
        if not identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect_to(url_for(controller='root', action='login', came_from=came_from,
                                login_counter=login_counter))
        userid = identity['repoze.who.userid']
        redirect_to(str(came_from))


