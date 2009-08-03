# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, check_testing
from republicaos.lib.auth import login_required, owner_required
from republicaos.lib.base import BaseController
from formencode import Schema, validators
from republicaos.lib.auth import check_user, get_user, set_user, owner_required
from republicaos.lib.auth import morador_ou_ex_required, morador_required, republica_required
from republicaos.lib.auth import republica_resource_required
from republicaos.model import TipoDespesa


import logging
log = logging.getLogger(__name__)

class TestController(BaseController):
    '''
    Só será habilitada durante os testes.
    '''
    def __before__(self):
        if not check_testing():
            abort(404)
    
    
    @login_required
    def requer_login(self):
        '''
        Tem de ser autenticado para acessar esse serviço
        '''
        return 'Tem de ser autenticado para acessar esse serviço'
    
    
    @owner_required
    def requer_owner(self, id):
        '''
        Para acessar esser recurso, tem de ser o dono
        '''
        return 'Para acessar esser recurso, tem de ser o dono'
    
    
    @republica_required
    def requer_republica(self, id):
        '''
        É necessário haver uma parte referente a republica_id na url
        '''
        return
    
    
    @morador_ou_ex_required
    def requer_morador_ou_ex(self, id):
        '''
        Apenas moradores e ex-moradores podem acessar esse recurso
        '''
        return 'Apenas moradores ou ex-moradores podem acessar esse recurso'
    
    
    
    @morador_required
    def requer_morador(self, id):
        '''
        Apenas morador pode acessar esse recurso
        '''
        return 'Apenas morador pode acessar esse recurso'


    @republica_resource_required(TipoDespesa)
    def requer_recurso_republica(self, id):
        '''
        O tipo de despesa sendo acessado tem de ser da república
        '''
        return
