# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from pylons import request, response, session, tmpl_context as c

from republicaos.model import Pessoa, Republica
from republicaos.lib.helpers import flash
from republicaos.lib.base import BaseController
from pylons.controllers.util import abort, redirect
from republicaos.lib.utils import encrypt

from pylons import config, url

from decorator import decorator
from pylons.controllers.util import abort

import logging

log = logging.getLogger(__name__)


# Abordagem mais simples para autenticação
# http://wiki.pylonshq.com/display/pylonscookbook/Simple+Homegrown+Authentication

# TODO: dar uma olhada na versão mais atual
# http://wiki.pylonshq.com/display/pylonscookbook/Advanced+Homegrown+Auth


def check_user(email, senha):
    return Pessoa.get_by(email=email, _senha=encrypt(senha))


def get_user():
    '''
    Obtém o usuário autenticado no sistema, se houver
    '''
    id = request.environ.get('REMOTE_USER') or session.get('userid')
    return Pessoa.get_by(id=id) if id else None
    

def get_republica():
    id = request.urlvars.get('republica_id')
    return Republica.get_by(id=id) if id else None
    


#
# É necessário que a configuração defina beaker.session.auto = True
#

def set_user(user = None):
    '''
    Define o usuário do sistema. Tipo um login feito por programação. Baseado em http://bugs.repoze.org/issue58
    '''
    if user != None:
        session['userid'] = user.id
        request.environ['REMOTE_USER'] = user.id
    else:
        session.pop('userid', None)
        request.environ.pop('REMOTE_USER', None)




@decorator
def login_required(func, self, *args, **kwargs):
    log.debug('login_required')
    c.user = get_user()
    if not c.user:
        session['came_from'] = request.path_info
        flash('Antes de continuar, é necessário entrar no sistema', 'info')
        redirect(url(controller='root', action='login'))
    return func(self, *args, **kwargs)


@decorator
@login_required
def owner_required(func, self, *args, **kwargs):
    log.debug('owner_required')
    log.debug("owner_required: request.urlvars['id']): %s, c.user.id: %s", request.urlvars['id'], c.user.id)
    if int(request.urlvars['id']) != c.user.id:
        abort(403, 'Só o proprietário desse recurso pode manipulá-lo.')
    return func(self, *args, **kwargs)


@decorator
def republica_required(func, self, *args, **kwargs):
    log.debug('republica_required')
    c.republica = get_republica()
    if not c.republica:
        erro = 'República inexistente ou não referenciada'
        flash(erro, 'error')
        abort(404, comment=erro)
    return func(self, *args, **kwargs)


user_status_morador = 1
user_status_ex_morador = 2


@decorator
@republica_required
@login_required
def morador_ou_ex_required(func, self, *args, **kwargs):
    log.debug('morador_ou_ex_required')
    # qual o status do usuário em relação à república

    if c.republica in c.user.morador_em_republicas:
        session['user_status'] = user_status_morador
    elif c.republica in c.user.ex_morador_em_republicas:
        session['user_status'] = user_status_ex_morador
    else:
        session.pop('user_status', None)
        erro = '(Recurso acessível apenas por moradores ou ex-moradores da república'
        #flash(erro, 'error')
        abort(403, detail=erro)
    return func(self, *args, **kwargs)


@decorator
@morador_ou_ex_required
def morador_required(func, self, *args, **kwargs):
    log.debug('morador_required')
    if session.get('user_status') != user_status_morador:
        abort(403, 'Só moradores da república têm acesso a este recurso.')
    return func(self, *args, **kwargs)



def republica_resource_required(entity, id='id', convert=lambda x: x):
    '''
    Recurso deve pertencer à republica sendo acessada.
    Já define o recurso ao objeto.
    '''
    @morador_required
    def _republica_resource_required(func, self, *args, **kwargs):
        # gambiarra pra ficar "genérica"
        resource = entity.get_by(**{str(id): convert(request.urlvars.get(id))})
        if not resource:
            abort(404)
        if not hasattr(resource, 'republica'):
            abort(406)
        if str(resource.republica.id) != request.urlvars['republica_id']:
            abort(403)
        setattr(c, entity.table.name, resource)
        return func(self, *args, **kwargs)
    return decorator(_republica_resource_required)
