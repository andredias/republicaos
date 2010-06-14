# -*- coding: utf-8 -*-
"""Setup the teste application"""
from __future__ import unicode_literals

import logging

import pylons.test
from republicaos import model as model
from republicaos.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup teste here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    model.metadata.create_all()
