# -*- coding: utf-8 -*-
import logging

from pylons import url, request, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.base import BaseController, render

log = logging.getLogger(__name__)

from repoze.what.predicates import has_permission
from republicaos import model as model
from republicaos.lib.helpers import flash
# from republicaos.lib.auth import require
from republicaos.lib.decorators import require

class LoginController(BaseController):

    def __before__(self):
        pass

    def index(self):
        c.users = model.Session.query(model.User).all()
        c.groups = model.Session.query(model.Group).all()
        c.permissions = model.Session.query(model.Permission).all()
        c.title = 'Test'
        c.identity = request.environ.get('repoze.who.identity', False)
        login_counter = request.environ.get('repoze.who.logins', 0)
        if login_counter > 0:
            c.flash = flash('Wrong credentials')
        c.login_counter = login_counter
        c.came_from = request.params.get('came_from') or url('/')
        return render('login.mak')
    

    def welcome_back(self):
        """
        Greet the user if he logged in successfully or redirect back to the login
        form otherwise.
        
        """
        identity = request.environ.get('repoze.who.identity')
        came_from = str(request.params.get('came_from', '')) or url('/')
        if not identity:
            # The user provided the wrong credentials
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect_to(url('/login', came_from=came_from,
                                __logins=login_counter))
        userid = identity['repoze.who.userid']
        c.flash = flash('Welcome back, %s!' % userid)
        redirect_to(came_from)
    

    def see_you_later(self):
        """Say goodbye to the user, she just logged out"""
        c.flash = flash('We hope to see you soon!')
        came_from = str(request.params.get('came_from', '')) or url('/')
        redirect_to(came_from)
    

    @require(has_permission('edit-posts'))
    def check_permission(self):
        message = "If you can see this, that's because you can edit posts"
        return message
    

