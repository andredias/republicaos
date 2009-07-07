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

    @dispatch_on(GET='get', POST='create', PUT='update', DELETE='delete')
    def rest_dispatcher(self, id):
        abort(404)

    # Métodos REST. A idéia é que não usem interface alguma. Equivalem a get/set de objetos

    @restrict("GET")
    def get(self, id):
        r = get_object_or_404(Republica, id = int(id))
        return r.to_dict()

    @restrict("POST")
    @validate(RepublicaSchema) # pra garantir
    def create(self):
        """POST /republica: Create a new item"""
        if not c.valid_data:
            abort(406)
        r = Republica(**c.valid_data)
        Session.commit()
        # TODO: estudar melhor qual vai ser o retorno dessa função. Analisar o header pra saber json, xml etc.
        return r

    @restrict("PUT")
    @validate(RepublicaSchema) # pra garantir
    def update(self, id):
        """PUT /republica/id: Update an existing item"""
        if not c.valid_data:
           abort(406)
        r = get_object_or_404(Republica, id = int(id))
        r.from_dict(c.valid_data)
        Session.commit()
        # TODO: estudar melhor qual vai ser o retorno dessa função. Analisar o header pra saber json, xml etc.
        return r

    @restrict("DELETE")
    def delete(self, id):
        """DELETE /republica/id: Delete an existing item"""
        abort(403)

    # Demais métodos relacionados à formulários
    
    def index(self, format='html'):
        """GET /republicas: All items in the collection"""
        c.republicas = Republica.query.order_by(Republica.nome).all()
        return render('republica/index.html')


    @validate(RepublicaSchema)
    def new(self, format='html'):
        """GET /republica/new: Form to create a new item"""
        if c.canceled:
            redirect_to(controller='republica', action='index')
        elif c.valid_data:
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
        if c.valid_data:
            request.method = 'PUT'
            self.update(id)
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            c.canceled = True # força o redirecionamento a seguir
        if c.canceled:
            redirect_to(controller='republica', action='show', id=id)
        elif not c.errors:
            filler_data = get_object_or_404(Republica, id = int(id)).to_dict()
        else:
            filler_data = request.params
        c.action = url_for(controller='republica', action='edit', id=id)
        c.title = 'Editar Dados da República'
        return render('republica/form.html', filler_data = filler_data)


    def show(self, id, format='html'):
        """GET /republica/id: Show a specific item"""
        r = get_object_or_404(Republica, id = int(id))
        c.title = 'República'
        return render('republica/form.html', filler_data = r.to_dict())

