# -*- coding: utf-8 -*-

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.auth import morador_required, get_republica, get_user
from republicaos.lib.auth import republica_resource_required
from republicaos.lib.utils import render, validate, pretty_decimal
from republicaos.lib.base import BaseController
from republicaos.lib.validators import DataNoFechamento, Number
from republicaos.model import Pessoa, Republica, TipoDespesa, Despesa, DespesaAgendada, Session
from formencode import Schema, validators, Invalid
from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)


class DataTermino(validators.DateConverter):
    def validate_python(self, value, state):
        validators.DateConverter.validate_python(self, value, state)
        data_ref = get_republica().intervalo_valido_lancamento[1]
        if value <= data_ref:
            raise Invalid("A data deve ser depois de %s" % format_date(data_ref), value, state)


class DespesaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    lancamento = DataNoFechamento(not_empty = True, get_republica=get_republica)
    quantia = Number(not_empty = True, min = 0.01)
    termino = DataTermino(month_style = 'dd/mm/yyyy')





class DespesaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""


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


    @republica_resource_required(Despesa)
    def delete(self, id):
        if not c.despesa.republica.fechamento_atual.data_no_intervalo(c.despesa.lancamento):
            flash('(error) Despesa com lançamento fora do fechamento corrente não pode ser excluída')
        else:
            c.despesa.delete()
            Session.commit()
            flash('(info) Despesa removida')
        redirect_to(controller='republica', action='show', republica_id=c.despesa.republica.id)


    #
    # Demais métodos relacionados à formulários
    #
    @restrict('GET')
    def index(self):
        c.tipos_despesa = Despesa.query.filter_by(republica = c.republica).order_by(Despesa.nome).all()
        return render('despesa/index.html')

    @morador_required
    @validate(DespesaSchema)
    def new(self):
        republica = get_republica()
        session['came_from'] = request.path_info
        c.title  = 'Novo Tipo de Despesa'
        c.action = url_for(controller='despesa', action='new', republica_id=republica.id)
        filler = {
                'pessoa_id' : get_user().id,
                'tipo_id' : 0,
                'lancamento' : format_date(date.today()),
                'agendamento' : False,
                }
        log.debug('\n\nnew: request.params: %s\n\n', request.params)
        log.debug('\n\nnew: c.errors: %s\n\n', c.errors)
        if c.valid_data:
            log.debug('new: %s', c.valid_data)
            c.valid_data['pessoa'] = Pessoa.get_by(id=request.params['pessoa_id'])
            c.valid_data['tipo'] = TipoDespesa.get_by(id=request.params['tipo_id'])
            despesa = Despesa(republica=republica, **c.valid_data)
            if request.params.get('agendamento') == 'True':
                log.debug("\n\nnew: DespesaAgendada")
                DespesaAgendada(
                        republica=republica,
                        proximo_lancamento=c.valid_data['lancamento'] + relativedelta(months=1),
                        **c.valid_data
                        )
            Session.commit()
            flash('(info) Despesa no valor de $ %s lancada com sucesso' % pretty_decimal(c.valid_data['quantia']))
        else:
            filler.update(request.params)

        return render('despesa/despesa.html', filler_data=filler)


    def show(self, id, format='html'):
        return render('despesa/form.html', filler_data = c.despesa.to_dict())

    @republica_resource_required(Despesa)
    @validate(DespesaSchema)
    def edit(self, id, format='html'):
        session['came_from'] = request.path_info
        if not c.despesa.republica.fechamento_atual.data_no_intervalo(c.despesa.lancamento):
            flash('(error) Não é permitido editar despesa com lançamento fora do fechamento corrente')
            redirect_to(controller='republica', action='show', republica_id=c.despesa.republica.id)
        if c.valid_data:
            log.debug('\nc.despesa: %r\n', c.despesa.to_dict())
            # complementa as chaves que faltam na validação para usar em from_dict
            c.valid_data['pessoa_id'] = request.params['pessoa_id']
            c.valid_data['tipo_id'] = request.params['tipo_id']
            c.despesa.from_dict(c.valid_data)
            Session.commit()
            flash('(info) Despesa alterada com sucesso')
            redirect_to(controller='republica', action='show', republica_id=c.despesa.republica.id)
        elif not c.errors:
            filler_data = c.despesa.to_dict()
            filler_data['lancamento'] = format_date(filler_data['lancamento'])
            filler_data['quantia'] = pretty_decimal(filler_data['quantia'])
        else:
            filler_data = request.params
        c.action = url_for(controller='despesa', action='edit', id=id,
                           republica_id=c.despesa.republica.id)
        c.title = 'Editar Despesa'
        return render('despesa/despesa.html', filler_data = filler_data)


    
