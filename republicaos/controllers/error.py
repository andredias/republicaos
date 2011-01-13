
import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal
from republicaos.lib.auth import get_user
from pylons import request, response, session, tmpl_context as c
from republicaos.lib.utils import render

from republicaos.lib.base import BaseController

import logging

log = logging.getLogger(__name__)


class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    def document(self):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        log.debug('resp: %s', dir(resp))
        c.code = resp.status_int or request.GET.get('code', '')
        c.message = resp.status or request.GET.get('message', '')
        c.user = get_user()
        log.debug('c.message: %r', c.message)
        return render('error/error.html')

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
