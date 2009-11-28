# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from republicaos.lib.helpers import get_object_or_404, url_for, flash
from republicaos.lib.utils import render, validate
from republicaos.lib.base import BaseController
from formencode import Schema, validators
from republicaos.lib.auth import check_user, set_user, owner_required, get_user
from genshi.core import Markup
from republicaos.lib.captcha import captcha
from hashlib import md5
from republicaos.lib.mail import send_email
from StringIO import StringIO


log = logging.getLogger(__name__)

class LoginSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    email = validators.Email(not_empty=True)
    senha = validators.UnicodeString(not_empty=True)

class FaleconoscoSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True)
    email = validators.Email(not_empty=True)
    assunto = validators.UnicodeString(not_empty=True)
    mensagem = validators.UnicodeString(not_empty=True)


class RootController(BaseController):

    def index(self):
        c.user = get_user()
        return render('root/index.html')

    @validate(LoginSchema)
    def login(self):
        if c.valid_data:
            user = check_user(c.valid_data['email'], c.valid_data['senha'])
            if user:
                set_user(user)
                destino = session.pop('came_from', url_for(controller='pessoa', action='painel', id=user.id))
                redirect_to(destino)
            else:
                flash('(warning) O e-mail e/ou a senha fornecidos não conferem')
        return render('root/login.html', filler_data=request.params)


    def logout(self):
        set_user(None)
        redirect_to(controller='root', action='index')
    
    
    def tour(self):
        return render('root/tour.html')
    
    @validate(FaleconoscoSchema)
    def faleconosco(self):
        c.user = get_user()
        if c.valid_data:
            # formulário foi postado
            # fazer algumas verificações adicionais
            if not c.user and md5(request.params['captcha'].strip()).hexdigest() != request.params['captcha_md5']:
                log.debug('RootController.faleconosco: captcha: %s, captcha_md5: %s' % (
                                request.params['captcha'].strip(), request.params['captcha_md5']))
                c.errors['captcha'] = 'Resposta incorreta'
            if not c.errors:
                # enviar mensagem
                text = StringIO()
                try:
                    text.write('Fale Conosco:\n')
                    for key, value in c.valid_data.items():
                        text.write('\n%s:\t%s' % (key, value))
                    text_message = text.getvalue()
                finally:
                    text.close()
                html_message = render('faleconosco/html_message.html')
                send_email(
                         to_address='info@republicaos.com.br',
                         subject='FaleConosco: %s' % Markup.escape(c.valid_data['assunto'], quotes=False),
                         message=text_message,
                         html_message=html_message,
                         from_address=(c.user and c.user.email) or c.valid_data['email']
                         )
                flash('(info) Mensagem enviada!')
                if c.user:
                    redirect_to(controller='pessoa', action='painel', id=c.user.id)
                else:
                    redirect_to(controller='root', action='index')
        c.captcha, c.captcha_md5 = captcha()
        log.debug('RootController.faleconosco: captcha: %s, captcha_md5: %s' % (c.captcha, c.captcha_md5))
        return render('faleconosco/faleconosco.html', filler_data=request.params)


