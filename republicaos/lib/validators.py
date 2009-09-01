# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from formencode import Invalid, Schema, validators
from datetime import date, timedelta
from babel.dates import parse_date, get_date_format, format_date
from babel.numbers import parse_decimal, NumberFormatError
from republicaos.lib.utils import pretty_decimal
import pylons

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

    validator = validators.Unique(model = Pessoa, attr = 'email')

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


class DataNoFechamento(validators.FancyValidator):
    '''
    Verifica se a data está no período do último fechamento da república, isto é [ultimo_fechamento, proximo_fechamento[
    func_get_republica é uma função para obter a república cujos parâmetros serão usados

    '''
    __unpackargs__ = ('get_republica',)
    get_republica = None

    messages = {
        'fora_dos_limites': _("A data deve estar entre %(data_inicial)s e %(data_final)s"),
        'badFormat': _('Please enter the date in the form %(format)s')
        }


    def validate_python(self, value, state):
        republica = self.get_republica() if callable(self.get_republica) else self.get_republica
        data_inicial, data_final = republica.intervalo_valido_lancamento
        log.debug('validate_python: data_inicial: %s, data_final: %s, value: %s', data_inicial, data_final, value)
        
        if not republica.fechamento_atual.data_no_intervalo(value):
            raise Invalid(
                    self.message('fora_dos_limites', state,
                                 data_inicial=format_date(data_inicial),
                                 data_final=format_date(data_final)), value, state)



    def to_python(self, value, state):
        try:
            # TODO: Se precisar mudar formato, passar outros parâmetros
            date = parse_date(value)
        except ValueError as error:
            raise Invalid(error.message, value, state)
        except:
            raise Invalid(self.message('badFormat', state, format=get_date_format().pattern), value, state)

        self.validate_python(date, state)
        return date



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
