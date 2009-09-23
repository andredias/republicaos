# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, extract_attributes, iso_to_date
from republicaos.lib.base import BaseController
from republicaos.lib.auth import get_user, get_republica, login_required, morador_required
from republicaos.model import Republica, Morador, Fechamento, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class RepublicaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    # TODO: definir tamanhos máximos
    nome         = validators.UnicodeString(not_empty=True, max=90)
    logradouro   = validators.UnicodeString(not_empty=True, max=150)
    complemento  = validators.UnicodeString()
    cidade       = validators.UnicodeString(not_empty=True, max=80)
    uf           = validators.UnicodeString(not_empty=True, max=2)


class RepublicaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    @login_required
    def __before__(self, id=None):
        if id:
            c.republica = get_object_or_404(Republica, id = id)
    
    
    @dispatch_on(GET='list', POST='create')
    def rest_dispatcher_collection(self):
        abort(406)

    @dispatch_on(GET='retrieve', PUT='update', DELETE='delete')
    def rest_dispatcher_single(self, id):
        abort(406)

    # Métodos REST. A idéia é que não usem interface alguma. Equivalem a get/set de objetos
    # CRUD - Create | Retrieve | Update | Delete

    @restrict("GET")
    def list(self):
        pass

    @restrict("POST")
    @validate(RepublicaSchema) # pra garantir
    def create(self):
        """POST /republica: Create a new item"""
        if not c.valid_data:
            abort(406)
        c.republica = Republica(**c.valid_data)
        Morador(pessoa=get_user(), republica=c.republica)
        Session.commit()
        # TODO: precisa retornar código 201 - Created
        response.status = 201 # Created
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.republica.to_dict()

    @restrict("PUT")
    @validate(RepublicaSchema) # pra garantir
    def update(self, id):
        """PUT /republica/id: Update an existing item"""
        if not c.valid_data:
           abort(406)
        c.republica.from_dict(c.valid_data)
        Session.commit()
        return

    @restrict("DELETE")
    def delete(self, id):
        """DELETE /republica/id: Delete an existing item"""
        abort(403)
        # se fosse permitido apagar, deveria retornar status 200 OK

    # Demais métodos relacionados à formulários

    def index(self):
        """GET /republica: All items in the collection"""
        c.republicas = Republica.query.order_by(Republica.nome).all()
        return render('republica/index.html')


    @validate(RepublicaSchema)
    def new(self):
        """GET /republica/new: Form to create a new item"""
        user = get_user()
        if len(user.morador_em_republicas) >= 2:
            flash('(warning) Você já está associado a duas repúblicas. Não é possível criar uma nova!')
        elif c.valid_data:
            self.create()
            flash('(info) República criada com sucesso!')
            redirect_to(controller='republica', action='show', republica_id=c.republica.id)
        c.action = url_for(controller='republica', action='new')
        c.title  = 'Criar Nova República'
        c.submit = 'Criar'
        return render('republica/form.html', filler_data=request.params)




    @validate(RepublicaSchema)
    def edit(self, id):
        """GET /republica/edit/id: Edit a specific item"""
        c.voltar_para = url_for(controller='republica', action='show', republica_id=id)
        if c.valid_data:
            request.method = 'PUT'
            self.update(id)
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(c.voltar_para)
        elif not c.errors:
            filler_data = c.republica.to_dict()
        else:
            filler_data = request.params
        c.action = url_for(controller='republica', action='edit', id=id)
        c.title = 'Editar Dados da República'
        c.submit = 'Alterar'
        return render('republica/form.html', filler_data = filler_data)

    @morador_required
    def show(self, republica_id):
        """GET /republica/id: Show a specific item"""
        data = request.params.get('data_fechamento', None)
        republica = get_republica()
        c.fechamento = Fechamento.get_by(data=iso_to_date(data), republica=republica) if data else republica.fechamento_atual
        c.fechamento.executar_rateio()
        
        # Só pode editar o fechamento atual
        c.read_only = c.fechamento.read_only
        return render('republica/index.html')
