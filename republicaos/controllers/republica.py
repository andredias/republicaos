# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.model import Republica, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class RepublicaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    # TODO: definir tamanhos máximos
    nome         = validators.UnicodeString(not_empty=True)
    logradouro   = validators.UnicodeString(not_empty=True)
    complemento  = validators.UnicodeString(not_empty=True)
    cidade       = validators.UnicodeString(not_empty=True)
    uf           = validators.UnicodeString(not_empty=True)
    cep          = validators.UnicodeString(not_empty=True)


class RepublicaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    
    def __before__(self, id=None):
        if id:
            c.republica = get_object_or_404(Republica, id = id)

    @dispatch_on(GET='get', POST='create', PUT='update', DELETE='delete')
    def rest_dispatcher(self, id):
        abort(404)

    # Métodos REST. A idéia é que não usem interface alguma. Equivalem a get/set de objetos

    @restrict("GET")
    def get(self, id):
        return c.republica.to_dict()

    @restrict("POST")
    @validate(RepublicaSchema) # pra garantir
    def create(self):
        """POST /republica: Create a new item"""
        if not c.valid_data:
            abort(406)
        r = Republica(**c.valid_data)
        Session.commit()
        # TODO: precisa retornar código 201 - Created
        response.status = "201 Created"
        return url_for(controller='republica', id=r.id)

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
    
    def index(self, format='html'):
        """GET /republicas: All items in the collection"""
        c.republicas = Republica.query.order_by(Republica.nome).all()
        return render('republica/index.html')


    @validate(RepublicaSchema)
    def new(self, format='html'):
        """GET /republica/new: Form to create a new item"""
        if c.valid_data:
            republica = self.create()
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(controller='republica', action='show', id=republica.id)
        c.action = url_for(controller='republica', action='new')
        c.title  = 'Nova República'
        return render('republica/form.html', filler_data=request.params)




    @validate(RepublicaSchema)
    def edit(self, id, format='html'):
        """GET /republica/edit/id: Edit a specific item"""
        if c.valid_data:
            request.method = 'PUT'
            self.update(id)
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(controller='republica', action='show', id=id)
        elif not c.errors:
            filler_data = c.republica.to_dict()
        else:
            filler_data = request.params
        c.action = url_for(controller='republica', action='edit', id=id)
        c.title = 'Editar Dados da República'
        return render('republica/form.html', filler_data = filler_data)


    def show(self, id, format='html'):
        """GET /republica/show/id: Show a specific item"""
        c.title = 'República'
        return render('republica/form.html', filler_data = c.republica.to_dict())
