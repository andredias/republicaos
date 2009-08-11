# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.lib.auth import morador_required, get_user, get_republica
from republicaos.model import Pessoa, Republica, Morador, ConviteMorador, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class MoradorSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True)
    email = validators.Email(not_empty=True) # TODO:problemas com unicode. Não dá pra usar resolve_domain=True ainda
    entrada = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)


class MoradorController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

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
    @validate(MoradorSchema) # pra garantir
    def create(self):
        """POST /pessoa: Create a new item"""
        if not c.valid_data:
            abort(406)
        c.pessoa = Morador(**c.valid_data)
        Session.commit()
        # TODO: precisa retornar código 201 - Created
        response.status = 201 # Created
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.pessoa.to_dict()

    @restrict("PUT")
    @validate(MoradorSchema) # pra garantir
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
        c.pessoas = Morador.query.order_by(Morador.nome).all()
        return render('pessoa/index.html')


    @morador_required
    @validate(MoradorSchema)
    def new(self):
        republica = get_republica()
        if c.valid_data:
            # validação adicional que não está sendo feita pelo MoradorSchema
            if (republica.ultimo_fechamento <= c.valid_data['entrada'] < 
                    republica.proximo_fechamento):
                ConviteMorador.convidar_moradores(
                            nomes=c.valid_data['nome'],
                            emails=c.valid_data['email'],
                            user=get_user(),
                            republica=republica,
                            entrada=c.valid_data['entrada']
                        )
                Session.commit()
                redirect_to(controller='republica', action='show', id=republica.id)
            else:
                c.errors['entrada'] = 'Data de entrada fora dos limites!'
            
        c.action = url_for(controller='morador', action='new',
                            republica_id=request.urlvars['republica_id'])
        c.submit = 'Enviar convite'
        #FIXME: problemas com unicode
        c.title = 'Convidar morador para republica %s' % republica.nome
        for key, value in c.errors.items():
            flash('(error) %s: %s' % (key, value))
        return render('morador/form.html', filler_data=request.params)





    @validate(MoradorSchema)
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
            log.debug('MoradorController.edit: c.errors: %r' % c.errors)
            filler_data = request.params
        c.action = url_for(controller='pessoa', action='edit', id=id)
        c.title = 'Editar Dados da Morador'
        return render('pessoa/form.html', filler_data = filler_data)


    def show(self, id):
        """GET /pessoa/show/id: Show a specific item"""
        c.title = 'Morador'
        return render('pessoa/form.html', filler_data = c.pessoa.to_dict())
    
