#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import *
from elixir import *
from tests.test_fechamento import TestFechamentoContas
from tests.test_morador import TestMorador
from tests.test_dividir_conta_telefone import TestDividirContaTelefone

t = TestFechamentoContas()
t.setup()
try:
	t.test_fechamento()
finally:
	t.teardown()
