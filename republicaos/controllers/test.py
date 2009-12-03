# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, testing_app
from republicaos.lib.auth import login_required, owner_required
from republicaos.lib.base import BaseController
from formencode import Schema, validators
from republicaos.lib.auth import owner_required
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
        if not testing_app():
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
        
    
    def info(self):
        '''
        Retorna mensagem de erro do tipo info
        '''
        flash('(info) Teste executado com sucesso')
        flash('(info) Outra mensagem de teste')
        flash('(info) e mais outra...')
        return render('test/test.html')
        
    
    def warning(self):
        '''
        Retorna mensagem de erro do tipo warning
        '''
        flash('(warning) Se liga!')
        flash('(warning) Outra mensagem de teste')
        flash('(warning) e mais outra...')
        return render('test/test.html')
        
    
    def error(self):
        '''
        Retorna mensagem de erro do tipo error
        '''
        flash('(error) PERIGO')
        flash('(error) Outra mensagem de teste')
        flash('(error) e mais outra...')
        return render('test/test.html')
    
    
    def mix(self):
        '''
        Retorna mensagem de erro do tipo error
        '''
        flash('(info) Teste executado com sucesso')
        flash('(warning) Se liga!')
        flash('(error) PERIGO')
        return render('test/test.html')