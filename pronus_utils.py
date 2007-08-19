# -*- coding: utf-8 -*-

from decimal    import Decimal
from turbogears import validators

_pretty_number = validators.Number().from_python

def arredonda(numero, referencia):
	if type(numero) is not Decimal:
		numero = Decimal(str(numero))
	if type(referencia) is not Decimal:
		referencia = Decimal(str(referencia))
	result = (numero / referencia).to_integral() * referencia
	return result.quantize(referencia)


def pretty_decimal(numero, arredondamento = Decimal('0.01')):
	numero = arredonda(numero, arredondamento)
	return _pretty_number(numero)


def pretty_number(numero):
	return _pretty_number(numero)


def float_equal(float1, float2, precision = 0.001):
	return abs(float(float1) - float(float2)) < precision