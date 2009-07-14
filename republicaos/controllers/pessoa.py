# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.model import Pessoa, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class PessoaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True)
    senha = validators.UnicodeString(not_empty=True)
    e_mail = validators.Email(not_empty=True) # TODO:problemas com unicode. Não dá pra usar resolve_domain=True ainda


class PessoaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    def __before__(self, id=None):
        if id:
            c.pessoa = get_object_or_404(Pessoa, id = id)

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
    @validate(PessoaSchema) # pra garantir
    def create(self):
        """POST /pessoa: Create a new item"""
        if not c.valid_data:
            abort(406)
        c.pessoa = Pessoa(**c.valid_data)
        Session.commit()
        # TODO: precisa retornar código 201 - Created
        response.status = 201 # Created
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.pessoa.to_dict()

    @restrict("PUT")
    @validate(PessoaSchema) # pra garantir
    def update(self, id):
        """PUT /pessoa/id: Update an existing item"""
        if not c.valid_data:
           abort(406)
        c.pessoa.from_dict(c.valid_data)
        Session.commit()
        return

    @restrict("DELETE")
    def delete(self, id):
        """DELETE /pessoa/id: Delete an existing item"""
        abort(403)
        # se fosse permitido apagar, deveria retornar status 200 OK

    # Demais métodos relacionados à formulários

    def index(self):
        """GET /pessoa: All items in the collection"""
        c.pessoas = Pessoa.query.order_by(Pessoa.nome).all()
        return render('pessoa/index.html')


    @validate(PessoaSchema)
    def new(self):
        """GET /pessoa/new: Form to create a new item"""
        if c.valid_data:
            pessoa = self.create()
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(controller='pessoa', action='show', id=c.pessoa.id)
        c.action = url_for(controller='pessoa', action='new')
        c.title  = 'Nova República'
        return render('pessoa/form.html', filler_data=request.params)




    @validate(PessoaSchema)
    def edit(self, id, format='html'):
        """GET /pessoa/edit/id: Edit a specific item"""
        if c.valid_data:
            request.method = 'PUT'
            self.update(id)
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(controller='pessoa', action='show', id=id)
        elif not c.errors:
            filler_data = c.pessoa.to_dict()
        else:
            filler_data = request.params
        c.action = url_for(controller='pessoa', action='edit', id=id)
        c.title = 'Editar Dados da Pessoa'
        return render('pessoa/form.html', filler_data = filler_data)


    def show(self, id):
        """GET /pessoa/show/id: Show a specific item"""
        c.title = 'Pessoa'
        return render('pessoa/form.html', filler_data = c.pessoa.to_dict())
