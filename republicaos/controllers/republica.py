# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url, flash
from republicaos.lib.utils import render, validate, extract_attributes, iso_to_date
from republicaos.lib.base import BaseController
from republicaos.lib.geolocation import geolocation
from republicaos.lib.auth import login_required, morador_required
from republicaos.model import Republica, Morador, Fechamento, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class RepublicaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    # TODO: definir tamanhos máximos
    nome = validators.UnicodeString(not_empty=True, max=90)
    endereco = validators.UnicodeString(not_empty=True)



class RepublicaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    @login_required
    def __before__(self, id=None):
        pass
    
    
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
    @validate(RepublicaSchema)  # pra garantir
    def create(self):
        """POST /republica: Create a new item"""
        if not c.valid_data:
            abort(406)
        c.republica = Republica(**c.valid_data)
        Morador(pessoa=c.user, republica=c.republica)
        Session.commit()
        # TODO: precisa retornar código 201 - Created
        response.status = 201  # Created
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.republica.to_dict()


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

    @login_required
    @validate(RepublicaSchema)
    def new(self):
        """GET /republica/new: Form to create a new item"""
        if len(c.user.morador_em_republicas) >= 2:
            flash('Você já está associado a duas repúblicas. Não é possível criar uma nova!', 'warning')
        elif c.valid_data:
            try:
                c.valid_data[str('latitude')], c.valid_data[str('longitude')] = geolocation(c.valid_data['endereco'])
            except ValueError as erro:
                c.errors['endereco'] = erro.message
            else:
                c.republica = Republica(**c.valid_data)
                Morador(pessoa=c.user, republica=c.republica)
                Session.commit()
                response.status = 201  # Created
                flash('República criada com sucesso!', 'info')
                redirect(url(controller='republica', action='show', republica_id=c.republica.id))
        c.action = url(controller='republica', action='new')
        c.title = 'Criar Nova República'
        c.submit = 'Criar'
        return render('republica/form.html', filler_data=request.params)



    @morador_required
    @validate(RepublicaSchema)
    def edit(self, id):
        """GET /republica/edit/id: Edit a specific item"""
        c.voltar_para = url(controller='republica', action='show', republica_id=id)
        if c.valid_data:
            try:
                c.valid_data[str('latitude')], c.valid_data[str('longitude')] = geolocation(c.valid_data['endereco'])
            except ValueError:
                c.errors['endereco'] = 'Forneça um endereço válido'
            else:
                request.method = 'PUT'
                c.republica.from_dict(c.valid_data)
                Session.commit()
                flash('Cadastro da república foi alterado com sucesso', 'info')
                redirect(c.voltar_para)

        filler_data = request.params or c.republica.to_dict()
        c.action = url(controller='republica', action='edit', id=id, republica_id=id)
        c.title = 'Editar Dados da República'
        c.submit = 'Alterar'
        return render('republica/form.html', filler_data = filler_data)

    @morador_required
    def show(self, republica_id):
        """GET /republica/id: Show a specific item"""
        data = request.params.get('data_fechamento', None)
        log.debug('republica.show: data: %s' % data)
        c.fechamento = Fechamento.get_by(data=iso_to_date(data), republica=c.republica) if data else c.republica.fechamento_atual
        c.fechamento.executar_rateio()
        
        # Só pode editar o fechamento atual
        c.read_only = c.fechamento.read_only
        return render('republica/index.html')
