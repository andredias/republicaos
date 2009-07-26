# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.model import Pendente, Session
from formencode import Schema, validators

log = logging.getLogger(__name__)


class ConfirmacaoController(BaseController):
    def cadastro(self, id):
        pass
    
    def convite(self, id):
        pass
