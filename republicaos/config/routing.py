# -*- coding: utf-8 -*-
"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    
    # República
    map.connect('/republicas',
                controller='republica',
                action='index',
                conditions=dict(method=['GET']))
    
    map.connect('/republica',
                controller='republica',
                action='create',
                conditions=dict(method=['POST']))
    map.connect('/republica/{id}',
                controller='republica',
                action='rest_dispatcher',
                requirements={'id':'\d+'})
    
#    map.connect('/republica/{id}',
#                controller='republica',
#                action='update',
#                conditions=dict(method=['PUT']),
#                requirements={'id':'\d+'})
#    map.connect('/republica/{id}',
#                controller='republica',
#                action='delete',
#                conditions=dict(method=['DELETE']),
#                requirements={'id':'\d+'})




    # República
    map.connect('/republica/{republica_id}/tipos_despesa',
                controller='tipo_despesa',
                action='index',
                conditions=dict(method=['GET']),
                requirements={'republica_id':'\d+'})
    map.connect('/republica/{republica_id}/tipo_despesa',
                controller='tipo_despesa',
                action='create',
                conditions=dict(method=['POST']),
                requirements={'republica_id':'\d+'})
    map.connect('/republica/{republica_id}/tipo_despesa/nova',
                controller='tipo_despesa',
                action='new',
                conditions=dict(method=['GET']),
                requirements={'republica_id':'\d+'})
    map.connect('/republica/{id}',
                controller='tipo_despesa',
                action='show',
                conditions=dict(method=['GET']),
                requirements={'republica_id':'\d+', 'id':'\d+'})
    map.connect('/republica/{republica_id}/tipo_despesa/{id}',
                controller='tipo_despesa',
                action='update',
                conditions=dict(method=['PUT']),
                requirements={'republica_id':'\d+', 'id':'\d+'})
    map.connect('/republica/{republica_id}/tipo_despesa/{id}',
                controller='tipo_despesa',
                action='delete',
                conditions=dict(method=['DELETE']),
                requirements={'republica_id':'\d+', 'id':'\d+'})
    map.connect('/republica/{republica_id}/tipo_despesa/{id}/editar',
                controller='tipo_despesa',
                action='edit',
                conditions=dict(method=['GET']),
                requirements={'republica_id':'\d+', 'id':'\d+'})



    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}',
                requirements={'id':'\d+'})

    return map
