from pylons import request, response
from repoze.what.plugins.quickstart import setup_sql_auth
from repoze.what.plugins.pylonshq import ActionProtector, ControllerProtector
from republicados import model as model
from republicaos.lib.helpers import flash


def get_user():
    """Return the current user's database object."""
    if 'repoze.who.identity' in request.environ:
        return request.environ.get('repoze.who.identity')['user']
    else:
        return None
    


def add_auth(app, skip_authentication):
    """
    Add authentication and authorization middleware to the ``app``.
    
    We're going to define post-login and post-logout pages to do some cool things.
    
    """
    return setup_sql_auth(app, model.User, model.Group, 
                          model.Permission, model.Session,
                          login_url='/login/index',
                          post_login_url='/login/welcome_back', 
                          post_logout_url='/login/see_you_later',
                          translations={'user_name': 'username',
                                        'group_name': 'name',
                                        'permission_name': 'name'},
                          skip_authentication=skip_authentication)


def authz_denial_handler(reason):
    """
    A repoze.what-pylons authorization denial handler.
    
    :param reason: The user-friendly message on why authorization was denied.
    
    For more information about denial handlers, check:
    http://code.gustavonarea.net/repoze.what-pylons/Manual/Protecting.html#using-denial-handlers
    
    """
    if response.status_int == 401:
        message = 'Oops, you have to login: %s' % reason
    else:
        identity = request.environ['repoze.who.identity']
        userid = identity['repoze.who.userid']
        message = "Come on, %s, you know you can't do that: %s" % (userid,
                                                                   reason)
    flash(message)
    abort(response.status_int, comment=reason)


def require(ActionProtector):
    """
    Protect controller actions with a :mod:`repoze.what` predicate checker.
    
    :func:`authz_denial_handler` is called when authorization is denied.
    
    For more information about action protectors, check:
    http://code.gustavonarea.net/repoze.what-pylons/Manual/Protecting.html#protecting-a-controller-action
    
    """
    
    default_denial_handler = staticmethod(authz_denial_handler)


def protect(ControllerProtector):
    """
    Class decorator for controller-wide authorization using a :mod:`repoze.what`
    predicate checker.
    
    :func:`authz_denial_handler` is called when authorization is denied.
    
    For more information about controller-wide protectors, check:
    http://code.gustavonarea.net/repoze.what-pylons/Manual/Protecting.html#protecting-a-controller
    
    """
    
    default_denial_handler = staticmethod(authz_denial_handler)


