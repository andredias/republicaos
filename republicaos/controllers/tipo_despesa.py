# -*- coding: utf-8 -*-

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for
from republicaos.lib.utils import render, validate
from republicaos.lib.base import BaseController
from republicaos.model import Republica, TipoDespesa, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class TipoDespesaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True)
    descricao = validators.UnicodeString(not_empty=False)


class TipoDespesaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    def __before__(self, republica_id, id = None):
        c.republica = get_object_or_404(Republica, id=republica_id)
        if id:
            c.tipo_despesa = get_object_or_404(TipoDespesa, id=id, republica_id=republica_id)


    @dispatch_on(GET='list', POST='create')
    def rest_dispatcher_collection(self):
        abort(406)

    @dispatch_on(GET='retrieve', PUT='update', DELETE='delete')
    def rest_dispatcher_single(self, id):
        abort(406)


    # Métodos REST. A idéia é que não usem interface alguma. Equivalem a get/set de objetos

    @restrict("GET")
    def list(self):
        pass

    @restrict("POST")
    @validate(TipoDespesaSchema) # pra garantir
    def create(self):
        """POST /tipos_despesa: Create a new item"""
        if not c.valid_data:
            abort(406)
        t = TipoDespesa(**c.valid_data)
        t.republica = c.republica
        Session.commit()
        response.status = "201 Created"
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.tipo_despesa.to_dict()

    @restrict("PUT")
    @validate(TipoDespesaSchema) # pra garantir
    def update(self, id):
        if not c.valid_data:
           abort(406)
        c.tipo_despesa.from_dict(c.valid_data)
        Session.commit()
        return


    @restrict("DELETE")
    def delete(self, id):
        abort(403)
        # se fosse permitido apagar, deveria retornar status 200 OK
        c.tipo_despesa.delete()
        Session.commit()
        return

    #
    # Demais métodos relacionados à formulários
    #
    @restrict('GET')
    def index(self):
        c.tipos_despesa = TipoDespesa.query.filter_by(republica = c.republica).order_by(TipoDespesa.nome).all()
        return render('tipo_despesa/index.html')

    @validate(TipoDespesaSchema)
    def new(self):
        if c.valid_data:
            tipo_despesa = self.create()
            redirect_to(controller='republica', action='show', id=c.republica.id)
        c.action = url_for(controller='tipo_despesa', action='new', republica_id=c.republica.id)
        c.title  = 'Novo Tipo de Despesa'
        return render('tipo_despesa/form.html', filler_data=request.params)


    def show(self, id, format='html'):
        return render('tipo_despesa/form.html', filler_data = c.tipo_despesa.to_dict())

    @validate(TipoDespesaSchema)
    def edit(self, id, format='html'):
        if c.valid_data:
            request.method = 'PUT'
            self.update(id)
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(controller='republica', action='show', id=c.republica.id)
        elif not c.errors:
            filler_data = c.tipo_despesa.to_dict()
        else:
            filler_data = request.params
        c.action = url_for(controller='tipo_despesa', action='edit', id=id,
                           republica_id=c.republica.id)
        c.title = 'Editar Tipo de Despesa'
        return render('tipo_despesa/form.html', filler_data = filler_data)
