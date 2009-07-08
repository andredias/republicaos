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
                 always_scan=config['debug'],
                 explicit=True) # veja http://pylonsbook.com/en/1.0/urls-routing-and-dispatch.html#route-memory)
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    
    #
    # República
    #
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



    #
    # Tipo de Despesa
    #
    map.connect('/republica/{republica_id}/tipos_despesa',
                controller='tipo_despesa',
                action='index',
                requirements={'republica_id':'\d+'},
                conditions=dict(method=['GET']))
    
    map.connect('/republica/{republica_id}/tipo_despesa',
                controller='tipo_despesa',
                action='create',
                conditions=dict(method=['POST']))
    
    map.connect('/republica/{republica_id}/tipo_despesa/{id}',
                controller='tipo_despesa',
                action='rest_dispatcher',
                requirements={'republica_id':'\d+', 'id':'\d+'})
    
    map.connect('/republica/{republica_id}/tipo_despesa/{action}',
                controller='tipo_despesa')
    map.connect('/republica/{republica_id}/tipo_despesa/{action}/{id}',
                controller='tipo_despesa',
                requirements={'republica_id':'\d+', 'id':'\d+'})


    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}', requirements={'id':'\d+'})

    return map
