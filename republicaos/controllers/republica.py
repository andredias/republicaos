import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from republicaos.lib.base import BaseController, render

log = logging.getLogger(__name__)

class RepublicaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('republica', 'republica')

    def index(self, format='html'):
        """GET /republica: All items in the collection"""
        # url('republica')

    def create(self):
        """POST /republica: Create a new item"""
        # url('republica')

    def new(self, format='html'):
        """GET /republica/new: Form to create a new item"""
        # url('new_republica')

    def update(self, id):
        """PUT /republica/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('republica', id=ID),
        #           method='put')
        # url('republica', id=ID)

    def delete(self, id):
        """DELETE /republica/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('republica', id=ID),
        #           method='delete')
        # url('republica', id=ID)

    def show(self, id, format='html'):
        """GET /republica/id: Show a specific item"""
        # url('republica', id=ID)

    def edit(self, id, format='html'):
        """GET /republica/id/edit: Form to edit an existing item"""
        # url('edit_republica', id=ID)
