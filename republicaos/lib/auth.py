# -*- coding: utf-8 -*-

from pylons import request, response
from repoze.what.plugins.pylonshq import ActionProtector, ControllerProtector
from republicaos.model import Pessoa, Session
from republicaos.lib.helpers import flash

from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin, SQLAlchemyUserMDPlugin
from repoze.who.plugins.friendlyform import FriendlyFormPlugin

from repoze.what.middleware import setup_auth
from repoze.what.plugins.sql import configure_sql_adapters

from pylons import config

from decorator import decorator
from pylons.controllers.util import abort
from repoze.what.authorize import check_authorization, NotAuthorizedError
from paste.httpexceptions import HTTPUnauthorized



import logging

log = logging.getLogger(__name__)
cookie_name = 'republicaos.com.br'

def get_user():
    """Return the current user's database object."""
    if 'repoze.who.identity' in request.environ:
        return request.environ.get('repoze.who.identity')['user']
    else:
        return None
        


def set_user(userid):
    '''
    Define o usuário do sistema. Tipo um login feito por programação. Baseado em http://bugs.repoze.org/issue58
    '''
    identity = {'repoze.who.userid': userid}
    headers = request.environ['repoze.who.plugins'][cookie_name].remember(request.environ, identity)
    for k, v in headers:
        response.headers.add(k, v)


def add_auth(app, skip_authentication):
    """
    Baseado no código-fonte de setup_sql_auth em repoze.what_quickstart quickstart.py
    """

    # Setting the repoze.who authenticators:
    sqlauth = SQLAlchemyAuthenticatorPlugin(Pessoa, Session)
    sqlauth.translations['user_name'] = 'email'
    sqlauth.translations['validate_password'] = 'check_password'

    cookie = AuthTktCookiePlugin(config['beaker.session.secret'], cookie_name)

    form = FriendlyFormPlugin(
        login_form_url = '/login',
        login_handler_path = '/login_handler',
        post_login_url = '/post_login',
        logout_handler_path = '/logout_handler',
        post_logout_url = '/',
        login_counter_name='login_counter',
        rememberer_name=cookie_name
        )

    # Setting up the repoze.who mdproviders:
    sql_user_md = SQLAlchemyUserMDPlugin(Pessoa, Session)
    sql_user_md.translations['user_name'] = 'email'

    group_adapters = permission_adapters = None

    middleware = setup_auth(
                    app,
                    group_adapters,
                    permission_adapters,
                    identifiers = [('main_identifier', form), (cookie_name, cookie)],
                    authenticators = [('sqlauth', sqlauth)],
                    challengers = [('form', form)],
                    mdproviders = [('sql_user_md', sql_user_md)],
                    log_level=logging.INFO,
                    skip_authentication=skip_authentication
                )
    return middleware



def require(predicate):
    """
    Make repoze.what verify that the predicate is met.

    :param predicate: A repoze.what predicate.
    :return: The decorator that checks authorization.

    """

    @decorator
    def check_auth(func, *args, **kwargs):
        environ = request.environ
        try:
            predicate.check_authorization(environ)
        except NotAuthorizedError, reason:
            # TODO: We should warn the user
            #flash(reason, status='warning')
            raise HTTPUnauthorized()


        return func(*args, **kwargs)
    return check_auth
