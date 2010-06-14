# -*- coding: utf-8 -*-

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators.rest import restrict
from republicaos.lib.helpers import get_object_or_404, url, flash
from republicaos.lib.utils import render, validate, extract_attributes, iso_to_date
from republicaos.lib.utils  import pretty_decimal
from republicaos.lib.base import BaseController
from republicaos.lib.auth import morador_required, republica_resource_required
from republicaos.model import Republica, Morador, Fechamento, DespesaAgendada, Session
from republicaos.controllers.despesa import DespesaSchema
from formencode import Schema, validators
from babel.dates import format_date
from republicaos.lib.validators import Date


log = logging.getLogger(__name__)

class LancamentoProgramadoController(BaseController):
    @republica_resource_required(DespesaAgendada)
    @validate(DespesaSchema)
    def edit(self, id):
        if c.valid_data:
            # gambiarra para aproveitar o mesmo Schema e também o mesmo formulário
            c.valid_data['proximo_lancamento'] = c.valid_data['lancamento']
            c.despesa_agendada.from_dict(c.valid_data)
            Session.commit()
            flash(u'(info) Lançamento atualizado!')
            redirect(controller='republica', action='show', republica_id=c.republica.id)
        filler_data = c.despesa_agendada.to_dict()
        filler_data['lancamento'] = format_date(filler_data['proximo_lancamento'])
        filler_data['quantia'] = pretty_decimal(filler_data['quantia'])
        filler_data = request.params.copy() or filler_data
        c.tipo_objeto = 'lancamento_programado'
        return render('despesa/despesa.html', filler_data = filler_data)
    
    @republica_resource_required(DespesaAgendada)
    def delete(self, id):
        c.despesa_agendada.delete()
        Session.commit()
        flash(u'(info) Lançamento excluído')
        redirect(controller='republica', action='show', republica_id=c.republica.id)
        