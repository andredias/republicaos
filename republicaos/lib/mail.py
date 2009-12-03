# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

from pylons import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os.path import split

import logging
log = logging.getLogger(__name__)

#FIXME: essa rotina deveria estar em utils.py, mas por algum motivo
# gera um erro na iniciação do pylons quando fica lá

def encode(text):
    '''
    Tenta evitar problemas com o unicode na hora de enviar para fora do sistema.
    '''
    return text.encode('utf-8') if isinstance(text, unicode) else text


def send_email(to_address, subject, message, html_message=None, from_address=None):
    '''
    Envia e-mail de acordo com a configuração do sistema.
    veja http://docs.python.org/library/email-examples.html para mais detalhes
    sobre o procedimento
    '''
    # se estiver testando, não envia e-mail de verdade
    # FIXME: não funciona com chamada a republicaos.lib.util.testing_app
    # foi necessário usar o código direto
    if split(config['__file__'])[-1] != 'test.ini':
        import smtplib
    else:
        # veja http://pypi.python.org/pypi/MiniMock
        from minimock import Mock, Printer
        from sys import stderr
        
        class Output(object):
            def write(self, text):
                log.debug(text)
        
        output = Printer(Output())
        smtplib = Mock('smtplib', tracker=output)
        smtplib.SMTP = Mock('smtplib.SMTP', tracker=output)
        smtplib.SMTP.mock_returns = Mock('smtp_connection', tracker=output)
    
    if not from_address:
        from_address = config['smtp_user']
    
    msg = MIMEMultipart('alternative')
    msg.set_charset('utf-8')
    msg['From'] = from_address
    msg['To'] = to_address if isinstance(to_address, basestring) else ', '.join(to_address)
    msg['Subject'] = encode(subject)
    
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    text = MIMEText(encode(message), 'plain')
    text.set_charset('utf-8')
    msg.attach(text)
    if html_message:
        html = MIMEText(html_message, 'html')
        html.set_charset('utf-8')
        msg.attach(html)

    server = smtplib.SMTP(config['smtp_server'])
    server.login(config['smtp_user'], config['smtp_password'])
    try:
        server.sendmail(from_address, to_address, msg.as_string())
    finally:
        server.quit()
    return

