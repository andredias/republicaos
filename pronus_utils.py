# -*- coding: utf-8 -*-

from decimal import Decimal

def arredonda(numero, referencia):
	if type(numero) is not Decimal:
		numero = Decimal(str(numero))
	if type(referencia) is not Decimal:
		referencia = Decimal(str(referencia))
	
	return (numero / referencia).to_integral() * referencia