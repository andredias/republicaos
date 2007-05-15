#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from tests.test_fechamento import *
from tests.test_morador import TestMorador
from tests.test_dividir_conta_telefone import TestDividirContaTelefone

t = TestDividirContaTelefone()
t.setup()
try:
	t.test_dividir_conta_caso_0()
finally:
	t.teardown()
