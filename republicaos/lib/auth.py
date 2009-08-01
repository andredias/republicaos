# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from pylons import request, response, session
from republicaos.model import Pessoa
from republicaos.lib.helpers import flash
from pylons.controllers.util import abort, redirect_to

from pylons import config

from decorator import decorator
from paste.httpexceptions import HTTPUnauthorized, HTTPForbidden



import logging

log = logging.getLogger(__name__)

def check_user(email, senha):
    return Pessoa.get_by(email=email, _senha=Pessoa.encrypt_senha(senha))


def get_user():
    '''
    Obtém o usuário autenticado no sistema, se houver
    '''
    return Pessoa.get_by(id=session['userid']) if 'userid' in session else None
    


def set_user(user = None):
    '''
    Define o usuário do sistema. Tipo um login feito por programação. Baseado em http://bugs.repoze.org/issue58
    '''
    log.debug('set_user(%s)', user)
    if user is None and 'userid' in session:
        del session['userid']
    else:
        session['userid'] = user.id
    session.save()



@decorator
def login_required(func, self, *args, **kwargs):
    if not get_user():
        session['came_from'] = request.path_info
        session.save()
        flash('(info) Antes de continuar, é necessário entrar no sistema')
        redirect_to(controller='root', action='login')
    return func(self, *args, **kwargs)


@decorator
@login_required
def owner_required(func, self, *args, **kwargs):
    user = get_user()
    if int(request.urlvars['id']) != user.id:
        raise HTTPForbidden(comment = '(error) Só o proprietário desse recurso pode manipulá-lo.')
    return func(self, *args, **kwargs)


