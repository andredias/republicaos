# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from formencode import Invalid, Schema, validators
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
