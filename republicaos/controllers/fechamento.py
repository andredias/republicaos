# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import redirect_to
from republicaos.lib.helpers import url_for, flash
from republicaos.lib.auth import morador_required, get_republica, get_user
from republicaos.lib.auth import republica_resource_required
from republicaos.lib.utils import render, validate, pretty_decimal, iso_to_date
from republicaos.lib.base import BaseController
from republicaos.lib import validators
from republicaos.model import Pessoa, Republica, Fechamento, Session
from formencode import Schema

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta

import logging

log = logging.getLogger(__name__)

def min_date():
    '''
    data mínima que pode ser aceita para criação/edição da data de fechamento.
    '''
    republica = get_republica()
    return republica.data_criacao + timedelta(days=1)


class FechamentoSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    
    data = validators.Date(not_empty=True, min=min_date)


class FechamentoController(BaseController):
    
    @morador_required
    @validate(FechamentoSchema)
    def new(self):
        '''
        Fechamento de qualquer data > republica.data_criação é válido
        veja especificação em wiki:Evento/MoradorCriaFechamento
        '''
        if c.valid_data:
            Fechamento(data=c.valid_data['data'], republica=get_republica())
            try:
                Session.commit()
                flash('(info) Fechamento criado com sucesso')
            except SQLAlchemyError as error:
                trata_erro_bd(error)
            destino = session.pop('came_from', 
                        url_for(
                            controller='republica',
                            action='show',
                            republica_id=request.urlvars['republica_id']
                        )
                    )
            redirect_to(destino)
        
        filler = request.params or {str('data'):format_date(date.today())}
        c.title = 'Criar Fechamento'
        c.submit = 'Criar'
        return render('fechamento/form.html', filler_data=filler)
    
    
    @republica_resource_required(Fechamento, id='data', convert=lambda x:iso_to_date(x))
    @validate(FechamentoSchema)
    def edit(self, data=None):
        if c.valid_data:
            c.fechamento.data = c.valid_data['data']
            fechamentos = get_republica().fechamentos
            # a edição da data pode mudar a ordem da lista de fechamentos
            fechamentos.sort(key=lambda obj: obj.data, reverse=True)
            if fechamentos[0].data > date.today():
                Session.commit()
                flash('(info) Data do fechamento alterada com sucesso')
                destino = session.pop('came_from', 
                        url_for(
                            controller='republica',
                            action='show',
                            republica_id=request.urlvars['republica_id']
                        )
                    )
                redirect_to(destino)
            else:
                Session.rollback()
                flash('(error) Data não foi alterada pois é necessário haver um fechamento futuro')
        
        filler = request.params or {str('data'):format_date(c.fechamento.data)}
        c.title = 'Editar Fechamento'
        c.submit = 'Alterar'
        return render('fechamento/form.html', filler_data=filler)
    
    
    @republica_resource_required(Fechamento, id='data', convert=lambda x:iso_to_date(x))
    # data=None para o caso de tentarem acessar diretamente /fechamento/delete/ sem passar republica_id
    def delete(self, data=None):
        republica = get_republica()
        fechamentos = republica.fechamentos
        fechamentos.remove(c.fechamento)
        if len(fechamentos) and fechamentos[0].data > date.today():
            c.fechamento.delete()
            Session.commit()
            flash('(info) Fechamento excluído com sucesso')
        else:
            flash('(error) Não foi possível excluir o fechamento pois é o único fechamento futuro que resta')

        destino = session.pop('came_from', 
                    url_for(
                        controller='republica',
                        action='show',
                        republica_id=republica.id
                    )
                )
        redirect_to(destino)
