"""Pylons environment configuration"""
import os

from genshi.template import TemplateLoader
from pylons.configuration import PylonsConfig
from sqlalchemy import engine_from_config

import republicaos.lib.app_globals as app_globals
import republicaos.lib.helpers
from republicaos.config.routing import make_map
import republicaos.model as model

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config = PylonsConfig()
    config.init_app(global_conf, app_conf, package='republicaos', paths=paths)
    
    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)  
    config['pylons.h'] = republicaos.lib.helpers
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)

    # Create the Genshi TemplateLoader
    config['pylons.app_globals'].genshi_loader = TemplateLoader(
        paths['templates'], auto_reload=True)
    
    # Setup the SQLAlchemy^W Elixir database engine
    engine = engine_from_config(config, 'sqlalchemy.')
    if model.elixir.options_defaults.get('autoload'):
        # Reflected tables
        model.elixir.bind = engine
        model.metadata.bind = engine
        model.elixir.setup_all()
    else:
        # Non-reflected tables
        model.init_model(engine)
    
    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    config['pylons.strict_tmpl_context'] = False
    return config
