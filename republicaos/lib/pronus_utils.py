# -*- coding: utf-8 -*-

from decimal    import Decimal
from formencode import validators

_pretty_number = validators.Number().from_python

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
