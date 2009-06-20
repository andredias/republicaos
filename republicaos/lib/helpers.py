# -*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
# Import helpers as desired, or define your own, ie:
# from webhelpers.html.tags import checkbox, password
from genshi.core import Markup
from webhelpers import *
from routes import url_for, redirect_to

# Scaffolding helper imports
from webhelpers.html.tags import *
from webhelpers.html import literal
from webhelpers.pylonslib import Flash
import sqlalchemy.types as types
flash = Flash()
# End of.
def wrap_helpers(localdict):
    """Wrap the helpers for use in Genshi templates"""
    def helper_wrapper(func):
        def wrapped_helper(*args, **kwargs):
            return Markup(func(*args, **kwargs))
        try:
            wrapped_helper.__name__ = func.__name__
        except TypeError:
            # Python < 2.4
            pass
        wrapped_helper.__doc__ = func.__doc__
        return wrapped_helper
    for name, func in localdict.iteritems():
        if (not callable(func) or
            not func.__module__.startswith('webhelpers.rails')):
            continue
        localdict[name] = helper_wrapper(func)

wrap_helpers(locals())

def get_object_or_404(model, **kw):
    from pylons.controllers.util import abort
    """
    Returns object, or raises a 404 Not Found is object is not in db.
    Uses elixir-specific `get_by()` convenience function (see elixir source: 
    http://elixir.ematia.de/trac/browser/elixir/trunk/elixir/entity.py#L1082)
    Example: user = get_object_or_404(model.User, id = 1)
    """
    obj = model.get_by(**kw)
    if obj is None:
        abort(404)
    return obj

