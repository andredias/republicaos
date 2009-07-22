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


import logging
log = logging.getLogger(__name__)


def get_user():
    """Return the current user's database object."""
    if 'repoze.who.identity' in request.environ:
        return request.environ.get('repoze.who.identity')['user']
    else:
        return None



def add_auth(app, skip_authentication):
    """
    Baseado no código-fonte de setup_sql_auth em repoze.what_quickstart quickstart.py
    """

    # Setting the repoze.who authenticators:
    sqlauth = SQLAlchemyAuthenticatorPlugin(Pessoa, Session)
    sqlauth.translations['user_name'] = 'email'
    sqlauth.translations['validate_password'] = 'check_password'

    cookie_name = 'republicaos_cookie'

    cookie = AuthTktCookiePlugin(config['beaker.session.secret'], cookie_name) # TODO: pegar o secret do config

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



#def authz_denial_handler(reason):
    #"""
    #A repoze.what-pylons authorization denial handler.

    #:param reason: The user-friendly message on why authorization was denied.

    #For more information about denial handlers, check:
    #http://code.gustavonarea.net/repoze.what-pylons/Manual/Protecting.html#using-denial-handlers

    #"""
    #if response.status_int == 401:
        #message = 'Oops, you have to login: %s' % reason
    #else:
        #identity = request.environ['repoze.who.identity']
        #userid = identity['repoze.who.userid']
        #message = "Come on, %s, you know you can't do that: %s" % (userid,
                                                                   #reason)
    #flash(message)
    #abort(response.status_int, comment=reason)


#class require(ActionProtector):
    #"""
    #Protect controller actions with a :mod:`repoze.what` predicate checker.

    #:func:`authz_denial_handler` is called when authorization is denied.

    #For more information about action protectors, check:
    #http://code.gustavonarea.net/repoze.what-pylons/Manual/Protecting.html#protecting-a-controller-action

    #"""

    #default_denial_handler = staticmethod(authz_denial_handler)


#class protect(ControllerProtector):
    #"""
    #Class decorator for controller-wide authorization using a :mod:`repoze.what`
    #predicate checker.

    #:func:`authz_denial_handler` is called when authorization is denied.

    #For more information about controller-wide protectors, check:
    #http://code.gustavonarea.net/repoze.what-pylons/Manual/Protecting.html#protecting-a-controller

    #"""

    #default_denial_handler = staticmethod(authz_denial_handler)




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
            abort(401)

        return func(*args, **kwargs)
    return check_auth
