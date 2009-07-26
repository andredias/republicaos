# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import smtplib
from pylons import config
from email.mime.text import MIMEText


#FIXME: essa rotina deveria estar em utils.py, mas por algum motivo
# gera um erro na iniciação do pylons quando fica lá

def encode(text):
    '''
    Tenta evitar problemas com o unicode na hora de enviar para fora do sistema.
    '''
    return text.encode('utf-8') if isinstance(text, unicode) else text


def send_email(to_address, subject, message, from_address=None):
    '''
    Envia e-mail de acordo com a configuração do sistema.
    veja http://docs.python.org/library/email-examples.html para mais detalhes
    sobre o procedimento
    '''
    if not from_address:
        from_address = config['smtp_user']

    msg = MIMEText(encode(message))
    msg.set_charset('utf-8')
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = encode(subject)

    server = smtplib.SMTP(config['smtp_server'])
    server.login(config['smtp_user'], config['smtp_password'])
    server.sendmail(from_address, to_address, msg.as_string())
    server.quit()
    return
