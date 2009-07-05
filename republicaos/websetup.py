# -*- coding: utf-8 -*-
"""Setup the republicaos application"""
import logging

from republicaos.config.environment import load_environment

log = logging.getLogger(__name__)

from pylons import config
from elixir import *
from republicaos import model as model

def setup_app(command, conf, vars):
    """Place any commands to setup republicaos here"""
    load_environment(conf.global_conf, conf.local_conf)
    import datetime
    import hashlib
    model.metadata.create_all()
    gadmin = model.user.Group(
            name = "Administrators",
            description = u"Administration group",
            created = datetime.datetime.utcnow(),
            active = True)
    model.Session.add(gadmin)
    # model.Session.commit()
    # Check the status
    g = model.Session.query(
            model.user.Group).filter_by(
                name="Administrators").all()
    assert len(g) == 1
    assert g[0] == gadmin
    admin = model.user.User(
                username = u"admin", 
                password=hashlib.sha1("admin").hexdigest(),
                password_check=hashlib.sha1("admin").hexdigest(), 
                email="admin@example.com",
                created = datetime.datetime.utcnow(),
                active = True)
    model.Session.add(admin)
    gadmin.users.append(admin)
    # model.Session.add(gadmin)
    model.Session.commit()
    # Check the status
    u = model.Session.query(
            model.user.User).filter_by(
                username=u"admin").all()
    assert len(u) == 1
    assert u[0] == admin
