#!/usr/bin/python
# -*- coding: utf-8 -*-

from turbogears import testutil, database, config
from elixir import objectstore
from republicaos.model.business import *

# testutil tenta carregar a configuração de test.cfg automaticamente. Contudo, se o teste
# não está sendo executado a partir da raiz do projeto, então test.cfg não será encontrado.
# A exceção KeyError não vai ser lançada pois o código abaixo define uma configuração padrão
# se não houver uma presente.
if 'sqlalchemy.dburi' not in config.config.configMap["global"]:
	config.config.configMap["global"]['sqlalchemy.dburi'] = 'sqlite:///:memory:'

database.bind_meta_data()

class BaseTest(object):
	url = 'sqlite:///:memory:'
	def setup(self):
		database.metadata.connect(self.url)
		database.metadata.create_all()
	
	
	def teardown(self):
		# we don't use cleanup_all because setup and teardown are called for
		# each test, and since the class is not redefined, it will not be
		# reinitialized so we can't kill it
		database.metadata.drop_all()
		objectstore.clear()