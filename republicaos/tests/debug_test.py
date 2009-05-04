#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('/projetos/andref/republicaos_model_elixir_06')
from test_model.test_dividir_conta_telefone import TestDividirContaTelefone

t = TestDividirContaTelefone()
t.setup()
try:
    t.test_dividir_conta_caso_00()
finally:
    t.teardown()
