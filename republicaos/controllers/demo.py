# -*- coding: utf-8 -*-
import logging

from pylons import request, tmpl_context as c
from pylons.controllers.util import abort

from republicaos.lib.base import BaseController, render

log = logging.getLogger(__name__)

import republicaos.model as model

from republicaos.lib.auth import require

from repoze.what.predicates import Any, is_user, has_permission, is_anonymous
from repoze.what.plugins.pylonshq import is_met

class DemoController(BaseController):

    def __before__(self):
        pass

    def index(self):
        c.users = model.Session.query(model.User).all()
        c.groups = model.Session.query(model.Group).all()
        c.permissions = model.Session.query(model.Permission).all()
        c.title = 'Test'
        c.identity = request.environ.get('repoze.who.identity', False)
        return render('test.mak')
    
    # Use the @require decorator thus:
    @require(Any(has_permission('edit-posts'), is_user('admin'))) 
    def privindex(self):
        # Or use in-action Permission checks ...
        if is_met(is_anonymous()):
            abort(401, 'You are not authenticated')
        c.identity = request.environ.get('repoze.who.identity')
        c.users = model.Session.query(model.User).all()
        c.groups = model.Session.query(model.Group).all()
        c.permissions = model.Session.query(model.Permission).all()
        c.title = 'Test'
        return render('test.mak')


