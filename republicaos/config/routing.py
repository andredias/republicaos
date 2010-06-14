# -*- coding: utf-8 -*-
"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map(config):
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
    map.connect('/republica/{republica_id}', # tem de ser republica_id por causa do get_republica()
                controller='republica',
                action='show',
                requirements={'republica_id':'\d+'})

    #
    # Pessoa
    #
    map.connect('/pessoa',
                controller='pessoa',
                action='rest_dispatcher_collection',
                conditions=dict(method=['GET', 'POST']))
    map.connect('/pessoa/{id}',
                controller='pessoa',
                action='rest_dispatcher_single',
                requirements={'id':'\d+'},
                conditions=dict(method=['GET', 'PUT', 'DELETE']))


    map.connect('/republica/{republica_id}/{controller}/{action}')
    map.connect('/republica/{republica_id}/{controller}/{action}/{id}',
                requirements={'republica_id':'\d+', 'id':'\d+'})

    map.connect('/republica/{republica_id}/fechamento/{action}/{data}',
                controller='fechamento')



    map.connect('/', controller='root', action='index')
    map.connect('/{action}', controller='root')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
