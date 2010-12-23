# -*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
# Scaffolding helper imports
from pylons import url
from webhelpers.pylonslib import Flash
import logging

log = logging.getLogger(__name__)

flash = Flash(categories=('success', 'info', 'warning', 'error'), default_category='success')

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
