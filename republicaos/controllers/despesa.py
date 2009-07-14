# -*- coding: utf-8 -*-

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for
from republicaos.lib.utils import render, validate
from republicaos.lib.base import BaseController
from republicaos.model import Republica, TipoDespesa, Despesa, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class DespesaSchema(Schema):
    data_vencimento = validators.DateConverter(month_style = 'dd/mm/yyyy', not_empty = True)
    data_termino    = validators.DateConverter(month_style = 'dd/mm/yyyy')
    quantia         = validators.Number(not_empty = True)
    tipo_despesa_id = validators.Int(not_empty = True)
    morador_id      = validators.Int(not_empty = True)
    #id_despesa      = validators.Int()


class DespesaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    def __before__(self, republica_id, id = None):
        c.republica = get_object_or_404(Republica, id=republica_id)
        if id:
            c.despesa = get_object_or_404(Despesa, id=id, republica_id=republica_id)


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
    @validate(DespesaSchema) # pra garantir
    def create(self):
        """POST /tipos_despesa: Create a new item"""
        if not c.valid_data:
            abort(406)
        t = Despesa(**c.valid_data)
        t.republica = c.republica
        Session.commit()
        response.status = "201 Created"
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.despesa.to_dict()

    @restrict("PUT")
    @validate(DespesaSchema) # pra garantir
    def update(self, id):
        if not c.valid_data:
           abort(406)
        c.despesa.from_dict(c.valid_data)
        Session.commit()
        return


    @restrict("DELETE")
    def delete(self, id):
        abort(403)
        # se fosse permitido apagar, deveria retornar status 200 OK
        c.despesa.delete()
        Session.commit()
        return

    #
    # Demais métodos relacionados à formulários
    #
    @restrict('GET')
    def index(self):
        c.tipos_despesa = Despesa.query.filter_by(republica = c.republica).order_by(Despesa.nome).all()
        return render('despesa/index.html')

    @validate(DespesaSchema)
    def new(self):
        if c.valid_data:
            despesa = self.create()
            redirect_to(controller='republica', action='show', id=c.republica.id)
        c.action = url_for(controller='despesa', action='new', republica_id=c.republica.id)
        c.title  = 'Novo Tipo de Despesa'
        return render('despesa/form.html', filler_data=request.params)


    def show(self, id, format='html'):
        return render('despesa/form.html', filler_data = c.despesa.to_dict())

    @validate(DespesaSchema)
    def edit(self, id, format='html'):
        if c.valid_data:
            request.method = 'PUT'
            self.update(id)
            # TODO: flash indicando que foi adicionado
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect_to(controller='republica', action='show', id=c.republica.id)
        elif not c.errors:
            filler_data = c.despesa.to_dict()
        else:
            filler_data = request.params
        c.action = url_for(controller='despesa', action='edit', id=id,
                           republica_id=c.republica.id)
        c.title = 'Editar Tipo de Despesa'
        return render('despesa/form.html', filler_data = filler_data)
