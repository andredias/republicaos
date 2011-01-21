# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from republicaos.lib.helpers import get_object_or_404, url, flash
from republicaos.lib.utils import render, validate
from republicaos.lib.base import BaseController
from formencode import Schema, validators
from republicaos.lib.auth import check_user, set_user, owner_required, get_user
from genshi.core import Markup
from republicaos.lib.captcha import captcha
from republicaos.lib.mail import send_email
from StringIO import StringIO
from republicaos.lib.validators import Captcha


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
    captcha = Captcha(resposta='captcha_md5', not_empty=True)


class FaleconoscoSemCaptchaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True)
    email = validators.Email(not_empty=True)
    assunto = validators.UnicodeString(not_empty=True)
    mensagem = validators.UnicodeString(not_empty=True)


class RootController(BaseController):

    def index(self):
        c.user = get_user()
        return render('root/home.html', filler_data=request.params)


    def home(self):
        return self.index()


    @validate(LoginSchema)
    def login(self):
        if c.valid_data:
            user = check_user(c.valid_data['email'], c.valid_data['senha'])
            if user:
                set_user(user)
                destino = session.pop('came_from', url(controller='pessoa', action='painel', id=user.id))
                redirect(destino)
            else:
                flash('O e-mail e/ou a senha fornecidos não conferem', 'error')
        return render('root/login.html')


    def logout(self):
        set_user(None)
        redirect(url(controller='root', action='index'))
    
    
    def funcionamento(self):
        return render('root/funcionamento.html')
    
    
    def politica_privacidade(self):
        return render('root/politica_privacidade.html')
    
    def termos_uso(self):
        return render('root/termos_uso.html')
    
    @validate(FaleconoscoSchema, alternative_schema=FaleconoscoSemCaptchaSchema, check_function=get_user)
    def faleconosco(self):
        c.user = get_user()
        if c.valid_data:
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
            flash('Mensagem enviada!', 'info')
            if c.user:
                redirect(url(controller='pessoa', action='painel', id=c.user.id))
            else:
                redirect(url(controller='root', action='index'))
        c.captcha, c.captcha_md5 = captcha()
        log.debug('RootController.faleconosco: captcha: %s, captcha_md5: %s' % (c.captcha, c.captcha_md5))
        return render('faleconosco/faleconosco.html', filler_data=request.params)
