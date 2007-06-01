#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('/home/andref/projetos/republicaos')
from republicaos.tests.test_model.test_conta_telefone import TestContaTelefone

t = TestContaTelefone()
t.setup()
try:
	t.test_importacao_csv_2()
finally:
	t.teardown()
