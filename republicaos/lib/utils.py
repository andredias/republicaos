# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import inspect
import formencode
from decorator import decorator
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import config
from pylons.templating import pylons_globals, render_genshi
from genshi.filters import HTMLFormFiller
from os.path import splitext
from decimal import Decimal


import logging

log = logging.getLogger(__name__)



def arredonda_decimal(numero, referencia):
    if type(numero) is not Decimal:
            numero = Decimal(str(numero))
    if type(referencia) is not Decimal:
            referencia = Decimal(str(referencia))
    result = (numero / referencia).to_integral() * referencia
    return result.quantize(referencia)

def arredonda(numero, referencia = 1):
    if type(numero) is Decimal or type(referencia) is Decimal:
        return arredonda_decimal(numero, referencia)
    else:
        return round(numero / referencia) * referencia


def arredonda_cima(numero, referencia = 1):
    quociente = numero / referencia
    sinal = 1 if quociente >= 0 else -1
    fracao = abs(quociente - int(quociente))
    ajuste = (1 if fracao > 0.01 else 0) * sinal
    return (int(quociente) + ajuste) * referencia


def pretty_decimal(numero, arredondamento = Decimal('0.01')):
    numero = arredonda(numero, arredondamento)
    return pretty_number(numero)


def pretty_number(numero):
    return _pretty_number(numero)


def float_equal(float1, float2, precision = 0.001):
    return abs(float(float1) - float(float2)) < precision


# deprecated pois elixir.Entity já possui um método to_dict
def extract_attributes(obj):
    attrs = {}
    for name in dir(obj):
        value = getattr(obj, name)
        if not name.startswith('_') and not inspect.isroutine(value):
            attrs[name] = value
    return attrs

# deprecated pois elixir.Entity já possui um método from_dict
def dict_to_attributes(attributes, object):
    for key, value in attributes.iteritems():
        if hasattr(object, key):
            setattr(object, key, value)



template_loader = config['pylons.app_globals'].genshi_loader


def render(template, filler_data = {}, method = 'xhtml', doctype = 'xhtml'):
    globs = pylons_globals()
    #log.debug("render | template: '%s', globs: %r, filler_data: %r, doctype: '%s'" % 
    #          (template, globs, filler_data, doctype))
    # A junção de globs com filler_data possibilita usar variáveis diretamente no template, sem ter de
    # usar 'c.variavel', já que o HTMLFormFiller só preenche formulários e não variáveis.
    # Atenção: É importante que filler_data não tenha atributos comuns com globs como, por exemplo,
    # 'url' que é uma função no pylons.
    globs.update(filler_data)
    tmpl  = template_loader.load(template)
    stream = tmpl.generate(**globs)
    if filler_data:
        stream = stream | HTMLFormFiller(data = filler_data)
    return stream.render(method, doctype=doctype)




def validate2(schema):
    '''
    decorator made by Matt Good. See http://paste.lisp.org/display/28756
    '''
    def _validate2(func, self, *args, **kwargs):
        if not request.method == 'POST':
            return func(self, *args, **kwargs)
        self.form_cancelled = '_cancel' in request.POST
        if self.form_cancelled:
            return func(self, *args, **kwargs)
        defaults = request.POST.copy()
        try:
            self.form_result = schema.to_python(defaults)
        except formencode.api.Invalid, e:
            c.errors = e.unpack_errors()
        else:
            c.errors = {}
        return func(self, *args, **kwargs)
    return decorator(_validate2)


def validate(schema):
    def _validate(func, self, *args, **kwargs):
        c.errors = {}
        c.canceled = 'cancel' in request.params
        #raise Exception()
        if not c.canceled:
            # validate data
            data = request.params.copy()
            try:
                c.valid_data = schema.to_python(data)
            except formencode.Invalid, e:
                c.errors = e.unpack_errors()
        return func(self, *args, **kwargs)
    
    return decorator(_validate)
