# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pylons import request
from formencode import Invalid, Schema, validators
from datetime import date, timedelta
from babel.dates import parse_date, get_date_format, format_date
from babel.numbers import parse_decimal, NumberFormatError
from republicaos.lib.utils import pretty_decimal
from republicaos.lib.auth import get_user
from hashlib import md5


import logging

log = logging.getLogger(__name__)

_ = validators._ # dummy translation string

# Custom schemas

class FilteringSchema(Schema):
    "Schema with extra fields filtered by default"
    filter_extra_fields = True
    allow_extra_fields = True

# Model-based validators


class Unique(validators.FancyValidator):

    """
    Verifica se o valor é único no banco de dados. Exemplo

    field = validators.Unique(model = Pessoa, attr = 'email')

    Durante a validação, se houver um ou mais registros no banco de dados para o atributo, então
    lança a Exceção.
    """

    __unpackargs__ = ('model', 'field')
    messages = {
        #FIXME: acentuação na mensagem
        'notUnique' : _("Valor ja registrado no banco de dados"),
    }


    def validate_python(self, value, state):
        if isinstance(self.attr, unicode):
            self.attr = str(self.attr)
        instance = self.model.get_by(**{self.attr : value})
        if instance:
           raise Invalid(self.message('notUnique', state), value, state)


validators.Unique = Unique


class Captcha(validators.FancyValidator):
    """
    Verifica se o usuário forneceu a reposta correta ao CAPCTHA. O validador deve receber o nome do campo do request.params com a resposta md5 do captcha:
    
    captcha = validators.Captcha(resposta='captcha_md5')
    
    Se há um usuário logado, então é possível aceitar captchas vazios
    """
    messages = { 'incorreta' : _('Resposta incorreta'), }
    
    def validate_python(self, value, state):
        log.debug('Captcha.validate_python: value: %s, resposta_md5: %s' % (value, request.params.get(self.resposta)))
        if md5(value.strip()).hexdigest() != request.params.get(self.resposta):
            raise Invalid(self.message('incorreta', state), value, state)



class Number(validators.FancyValidator):
    '''
    validators.Number não está funcionando direito.
    '''
    messages = {
        'tooLow': "Forneça um número que seja %(min)s ou maior",
        'tooHigh': "Forneça um número que seja %(max)s ou menor",
        'number': "Forneça um número válido",
    }

    min = None
    max = None

    def validate_python(self, value, state):
        if self.min is not None:
            if value < self.min:
                msg = self.message("tooLow", state, min=pretty_decimal(self.min))
                raise Invalid(msg, value, state)
        if self.max is not None:
            if value > self.max:
                msg = self.message("tooHigh", state, max=pretty_decimal(self.max))
                raise Invalid(msg, value, state)
    
    
    def _to_python(self, value, state):
        try:
            return parse_decimal(value)
        except NumberFormatError:
            raise Invalid(self.message('number', state), value, state)



class Date(validators.FancyValidator):
    '''
    validators.DateConverter e DateValidator não estão atendendo
    '''
    min = None
    max = None
    
    messages = {
        'tooLow': "Forneça uma data igual à %(min)s ou posterior",
        'tooHigh': "Forneça uma data que igual à  %(max)s ou anterior",
        'invalido': "Forneça uma data válida",
    }
    
    def validate_python(self, value, state):
        if self.min:
            min = self.min() if callable(self.min) else self.min
            if value < min:
                msg = self.message("tooLow", state, min=format_date(min))
                raise Invalid(msg, value, state)
        if self.max:
            max = self.max() if callable(self.max) else self.max
            if value > max:
                msg = self.message("tooHigh", state, max=format_date(max))
                raise Invalid(msg, value, state)
    
    
    def _to_python(self, value, state):
        try:
            return parse_date(value)
        except:
            raise Invalid(self.message('invalido', state), value, state)
