# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import inspect
import re
import formencode
from decorator import decorator
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons import config
from pylons.templating import pylons_globals, render_genshi
from genshi.filters import HTMLFormFiller
from os.path import split
from decimal import Decimal
from babel.numbers import format_number, format_decimal, format_percent
from datetime import date
from unicodedata import normalize
from hashlib import sha1

from republicaos.lib.helpers import flash


import logging

log = logging.getLogger(__name__)


def testing_app():
    '''
    Verifica se o estado da execução do sistema está em teste.
    '''
    from pylons.test import pylonsapp
    return pylonsapp is not None


def debugging_app():
    '''
    Verifica se o estado da execução do sistema está em teste.
    '''
    return not testing_app()


def arredonda_decimal(numero, referencia):
    if type(numero) is not Decimal:
            numero = Decimal(str(numero))
    if type(referencia) is not Decimal:
            referencia = Decimal(str(referencia))
    result = (numero / referencia).to_integral() * referencia
    return result.quantize(referencia)


def arredonda(numero, referencia=1):
    if isinstance(numero, Decimal) or isinstance(referencia, Decimal):
        return arredonda_decimal(numero, referencia)
    else:
        return round(numero / referencia) * referencia


def arredonda_cima(numero, referencia=1):
    quociente = numero / referencia
    sinal = 1 if quociente >= 0 else - 1
    fracao = abs(quociente - int(quociente))
    ajuste = (1 if fracao > 0.01 else 0) * sinal
    return (int(quociente) + ajuste) * referencia


formato = "#,##0.00"


def pretty_decimal(numero, arredondamento=0.01):
#    numero = arredonda(numero, arredondamento)
    return format_decimal(numero, formato)


def pretty_number(numero):
    return _pretty_number(numero, locale='pt_BR')


def float_equal(float1, float2, precision=0.001):
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


def render(template, filler_data={}, method='xhtml', doctype='xhtml'):
    globs = pylons_globals()
    #log.debug("render | template: '%s', globs: %r, filler_data: %r, doctype: '%s'" %
    #          (template, globs, filler_data, doctype))
    # A junção de globs com filler_data possibilita usar variáveis diretamente no template, sem ter de
    # usar 'c.variavel', já que o HTMLFormFiller só preenche formulários e não variáveis.
    # Atenção: É importante que filler_data não tenha atributos comuns com globs como, por exemplo,
    # 'url' que é uma função no pylons.
    globs.update(filler_data)
    template_loader = config['pylons.app_globals'].genshi_loader
    tmpl = template_loader.load(template)
    stream = tmpl.generate(**globs)
    if filler_data:
        stream = stream | HTMLFormFiller(data=filler_data)
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


def validate_(schema):
    '''
    versão anterior da rotina validate
    '''
    def _validate(func, self, *args, **kwargs):
        c.errors = {}
        if request.method.lower() in ['post', 'put']:
            data = request.params.copy()
            try:
                c.valid_data = schema.to_python(data)
            except formencode.Invalid, e:
                c.errors = e.unpack_errors()
        return func(self, *args, **kwargs)

    return decorator(_validate)


def validate(schema, alternative_schema=None, check_function=None):
    '''
    Se só for passado um schema, usa este. Caso haja uma função de checagem,
    então é possível usar um ou outro esquema dependendo do resultado de check_function
    '''
    def _validate(func, self, *args, **kwargs):
        c.errors = {}
        if request.method.lower() in ['post', 'put']:
            data = request.params.copy()
            try:
                c.valid_data = alternative_schema.to_python(data) \
                        if callable(check_function) and check_function() else schema.to_python(data)
            except formencode.Invalid, e:
                c.errors = e.unpack_errors()
                log.debug('errors: %s', c.errors)
        return func(self, *args, **kwargs)

    return decorator(_validate)


def get_flash_messages():
    '''
    Agrupa as mensagens enviadas para flash em um dicionário de acordo com a categoria das mensagens.
    '''
    messages = flash.pop_messages()
    result = {}
    for message in messages:
        result.setdefault(message.category, []).append(message.message)
    return result


def iso_to_date(text):
    return date(*[int(num) for num in text.split('-')])


def rem_acentuacao(str):
    '''
    O código retira a acentuação das letras substituindo por caracteres simples. De: ã por a, ç por c e assim por diante.
    Retirado de http://www.jarbs.com.br/como-remover-a-acentuacao-das-strings-em-python,165.html
    '''
    return normalize('NFKD', str.decode('utf-8')).encode('ASCII', 'ignore')


def strtourl(str):
    '''
    Retira acentos, substitui espaços e caracteres diferentes de letras por “-” (hífen), e retorna uma string formatada para ser utilizada em URLs.
    veja http://www.jarbs.com.br/urls-amigaveis-em-python,161.html
    '''
    return re.sub('[^a-z0-9]+', '-',
                  normalize('NFKD', str.decode('utf-8')).encode('ASCII', 'ignore').lower())


def encrypt(*args):
    #FIXME: excluir a linha abaixo na versão 1.0.1 do Pylons, quando config já virá populado
    if testing_app():
        config['beaker.session.secret'] = '43210'
    # fim do trecho a se excluído
    
    palavra = ''.join(args).join(config['beaker.session.secret'])
    return sha1(palavra.encode('utf-8')).hexdigest()
