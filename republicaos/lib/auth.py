# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from pylons import request, response, session
from republicaos.model import Pessoa, Republica
from republicaos.lib.helpers import flash
from republicaos.lib.base import BaseController
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
    id = request.environ.get('REMOTE_USER') or session.get('userid')
    return Pessoa.get_by(id=id) if id else None
    

#
# É necessário que a configuração defina beaker.session.auto = True
#

def set_user(user = None):
    '''
    Define o usuário do sistema. Tipo um login feito por programação. Baseado em http://bugs.repoze.org/issue58
    '''
    if user is None and 'userid' in session:
        del session['userid']
        request.environ.pop('REMOTE_USER', None)
    else:
        session['userid'] = user.id
        request.environ['REMOTE_USER'] = user.id



@decorator
def login_required(func, self, *args, **kwargs):
    log.debug('login_required')
    if not get_user():
        session['came_from'] = request.path_info
        flash('(info) Antes de continuar, é necessário entrar no sistema')
        redirect_to(controller='root', action='login')
    return func(self, *args, **kwargs)


@decorator
@login_required
def owner_required(func, self, *args, **kwargs):
    log.debug('owner_required')
    user = get_user()
    log.debug("owner_required: request.urlvars['id']): %s, user.id: %s", request.urlvars['id'], user.id)
    if int(request.urlvars['id']) != user.id:
        raise HTTPForbidden(comment = '(error) Só o proprietário desse recurso pode manipulá-lo.')
    return func(self, *args, **kwargs)


@decorator
def republica_required(func, self, *args, **kwargs):
    id = request.urlvars.get('republica_id')
    republica = Republica.get_by(id=id)
    if not id or not republica:
        erro = '(error) República inexistente ou não referenciada'
        flash(erro)
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
    user = get_user()
    republica = Republica.get_by(id=request.urlvars.get('republica_id'))
    if republica in user.morador_em_republicas():
        session['user_status'] = user_status_morador
    elif republica in user.ex_morador_em_republicas():
        session['user_status'] = user_status_ex_morador
    else:
        session.pop('user_status')
        erro = '(error) Recurso acessível apenas por moradores ou ex-moradores da república'
        flash(erro)
        abort(403, comment=erro)
    return func(self, *args, **kwargs)


@decorator
@morador_ou_ex_required
def morador_required(func, self, *args, **kwargs):
    log.debug('morador_required')
    if session.get('user_status') != user_status_morador:
        raise HTTPForbidden(comment = '(error) Só moradores da república têm acesso a este recurso.')
    return func(self, *args, **kwargs)



def republica_resource_required(entity):
    '''
    Recurso deve pertencer à republica sendo acessada.
    Já define o recurso ao objeto.
    '''
    @morador_required
    def _republica_resource_required(func, self, *args, **kwargs):
        id = request.urlvars.get('id')
        if id:
            resource = entity.get_by(id=id)
            setattr(self, entity.table.name, resource)
            if not resource:
                abort(404)
            if not hasattr(resource, 'republica'):
                abort(406)
            if str(resource.republica.id) != request.urlvars['republica_id']:
                abort(403)
        return func(self, *args, **kwargs)
    return decorator(_republica_resource_required)
