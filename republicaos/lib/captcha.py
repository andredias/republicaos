# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

from hashlib import md5
import random
from republicaos.lib.utils import testing_app


def palavra():
    palavras = ['pronus', 'software', 'email', 'republicaos', 'abcdefg', 'hijklmn', 'opqrst',
                'uvxwz', 'python', 'design']
    palavra = random.choice(palavras)
    posicao = random.randint(1, len(palavra))
    resposta = md5(palavra[posicao - 1]).hexdigest()
    pergunta = 'Qual a %sª letra da palavra "%s"?' % (posicao, palavra)
    return (pergunta, resposta)


def conta():
    numeros = ['zero',
                'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez']
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    if random.randint(0, 1):
        operacao = 'vezes'
        resposta = md5(str(num1 * num2)).hexdigest()
    else:
        operacao = 'mais'
        resposta = md5(str(num1 + num2)).hexdigest()
    pergunta = 'Quanto é %s %s %s?' % (random.choice([num1, numeros[num1]]),
                                        operacao,
                                        random.choice([num2, numeros[num2]]))
    return (pergunta, resposta)


def maior_menor():
    numeros = random.sample(xrange(100), 4)
    if random.randint(0, 1):
        comparacao = 'maior'
        resposta = md5(str(max(numeros))).hexdigest()
    else:
        comparacao = 'menor'
        resposta = md5(str(min(numeros))).hexdigest()
    pergunta = 'Qual o %s número da lista %s?' % (comparacao, numeros)
    return (pergunta, resposta)


def captcha():
    if not testing_app():
        return random.choice([palavra, conta, maior_menor])()
    else:
        pergunta = 'Quanto é 1 + 1?'
        resposta = md5('2').hexdigest()
        return (pergunta, resposta)
