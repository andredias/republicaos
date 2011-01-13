#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

from decimal import Decimal
from republicaos.lib.utils import pretty_decimal
import sys
import codecs

(e, d, sr, sw) = codecs.lookup('utf-8')
unicode_to_utf8 = sw(sys.stdout)
write = unicode_to_utf8.write


def print_rateio_conta_telefone(conta):
    write('\n\nRATEIO CONTA DE TELEFONE\n------------------------')
    write('\nTotal Conta = %s' % conta.total)
    write('\nFranquia = %s' % conta.franquia)
    write('\nServiços = %s' % conta.servicos)
    write('\nTelefonemas = %s' % conta.total_telefonemas)

    campos = ('quota', 'franquia', 'gastos', 'extras', 'devido', 'excedente', 'abono', 'a_pagar')
    funcoes = (conta.fechamento.quota, conta.rateio.franquia, conta.rateio.telefonemas, conta.rateio.extras,
                conta.rateio.devido, conta.rateio.excedente, conta.rateio.abono, conta.rateio.a_pagar)
    totais = [Decimal(0) for i in range(len(funcoes))]
    write('\n\n----------|%9s|%9s|%9s|%9s|%9s|%9s|%9s|%9s' % campos)
    moradores = list(conta.participantes)
    moradores.sort()
    for morador in moradores:
        write('\n%10s' % morador.pessoa.nome)
        for i in range(len(funcoes)):
            resultado = funcoes[i](morador)
            totais[i] += resultado
            write('|%9.2f' % resultado)

    # mostra totais
    write('\n----------')
    for i in range(len(totais)):
        write('|%9.2f' % totais[i])
    write('\n\n')
    sys.stdout.flush()


def print_resumo_despesas(fechamento):
    write('\n\nRESUMO DAS DESPESAS\n-------------------\nTipo           |  Total')
    tipos_despesa = sorted(fechamento.total_tipo_despesa.keys())
    for tipo_despesa in tipos_despesa:
        write('\n%15s| %.2f' % (tipo_despesa.nome, fechamento.total_tipo_despesa[tipo_despesa]))
    write('\n\n%*s = %*s' % (19, 'Total Geral', 7, pretty_decimal(fechamento.total_despesas)))
    write('\n%*s = %*d' % (19, 'Número de moradores', 4, len(fechamento.participantes)))
    write('\n%*s = %*.2f' % (19, 'Média', 7, \
        (fechamento.total_despesas / (len(fechamento.participantes) if len(fechamento.participantes) else 1))))


def print_despesas(fechamento):
    write('\n\nRELAÇÃO DE DESPESAS\n-------------------\n')
    write('| %-*s| %-*s| %-*s| %s' % (11, 'Data', 9, 'Valor', 15, 'Tipo Despesa', 'Responsável'))
    for despesa in fechamento.despesas:
        write('\n| %s | %*.2f | %-*s| %s' % (despesa.data, 8, despesa.quantia, 15, despesa.tipo.nome, despesa.pessoa.nome))
    write('\n')


def print_rateio(fechamento):
    write('\n\nRATEIO\n------\n')
    write(' %-*s| %-*s| %-*s|'
        #' %-*s|'
        ' %-*s| %s' %
        (
        9, 'Morador',
        12, 'Participação',
        8, 'Quota',
#        8, 'Telefone',
        8, 'Despesas',
        'Saldo Final'
        )
    )
    for participante in fechamento.participantes:
        write('\n %*s| %*s%%| %*s| %*s| %*s| %*s' % \
            (9, participante.pessoa.nome,
            11, pretty_decimal(fechamento.quota[participante], 1),
            8, pretty_decimal(fechamento.rateio[participante]),
#            8, pretty_decimal(fechamento.total_telefone[participante]),
            8, pretty_decimal(fechamento.despesas[participante]),
            8, pretty_decimal(fechamento.saldo_final[participante]))
        )

    total_porcentagem = sum(fechamento.porcentagem[participante] for participante in fechamento.participantes)
    total_quotas = sum(fechamento.quota[participante] for participante in fechamento.participantes)
    total_saldo_final = sum(fechamento.saldo_final[participante] for participante in fechamento.participantes)
    write('\n %*s| %*s%%| %*s|'
#        ' %*s|'
        ' %*s| %*s' %
        (
        9, 'TOTAL  ',
        11, pretty_decimal(total_porcentagem, 1),
        8, pretty_decimal(total_quotas),
#        8, pretty_decimal(fechamento.total_telefone()),
        8, pretty_decimal(fechamento.total_despesas),
        8, pretty_decimal(total_saldo_final)
        )
    )
    write('\n\n')


def print_acerto_final(fechamento):
    write('\nACERTO DAS CONTAS\n-----------------')
    write('\n%10s' % ' ')
    for pessoa in fechamento.participantes:
        write('|%10s' % pessoa.nome)
    write('| Total a Pagar')

    for devedor in fechamento.participantes:
        write('\n%10s' % devedor.nome)
        total_a_pagar = Decimal(0)
        if devedor not in fechamento.acerto_a_pagar:
            write(('|%10s' % ' ') * (len(fechamento.participantes) + 1))
        else:
            for credor in fechamento.participantes:
                if credor in fechamento.acerto_a_pagar[devedor]:
                    a_pagar = fechamento.acerto_a_pagar[devedor][credor]
                    total_a_pagar += a_pagar
                    write('|%10s' % pretty_decimal(a_pagar))
                else:
                    write('|%10s' % ' ')
            write('|%10s' % pretty_decimal(total_a_pagar))
    write('\n%s' % ('-' * 10 * (len(fechamento.participantes) + 3)))
    write('\n   Receber')
    for credor in fechamento.participantes:
        if credor in fechamento.acerto_a_receber:
            write('|%10s' % pretty_decimal(sum(fechamento.acerto_a_receber[credor].values())))
        else:
            write('|%10s' % ' ')
    write('\n\n\n')



def print_fechamento(fechamento):
    write('=' * 50)
    print_resumo_despesas(fechamento)
    print_despesas(fechamento)
    print_rateio(fechamento)
    print_acerto_final(fechamento)
    sys.stdout.flush()



def print_calculo_quotas_participantes(fechamento):
    write('\n\nCÁLCULO DAS QUOTAS DO FECHAMENTO\n-----------------')
    write('\nData Inicial: %s | Data Final: %s' % (fechamento.data_inicial.strftime('%d/%m/%Y'), fechamento.data_final.strftime('%d/%m/%Y')))
    write('\nTotal de dias: %d' % fechamento.total_dias_morados)
    write('\nParticipantes | Peso(%) | Quota(%) | Quota_Peso(%)')
    total_peso = 0
    total_quota = 0
    total_quota_peso = 0
    for participante in fechamento.participantes:
        peso = participante.peso_quota(fechamento.data_inicial)
        quota = fechamento.quota[participante]
        quota_peso = fechamento.quota_peso[participante]
        total_peso += peso
        total_quota += quota
        total_quota_peso += quota_peso
        write('\n%14s|%9.2f|%9.2f |%9.2f' % (participante.pessoa.nome, participante.peso_quota(fechamento.data_inicial), quota, quota_peso))
    write('\n%14s|%9.2f|%9.2f |%9.2f\n\n' % (' TOTAL', total_peso, total_quota, total_quota_peso))
    write('\n\nIntervalos:')
    for intervalo in fechamento.intervalos:
        write('\n\t--------------')
        write('\n\tData Inicial: %s | Data Final: %s' % (intervalo.data_inicial.strftime('%d/%m/%Y'), intervalo.data_final.strftime('%d/%m/%Y')))
        write('\n\tNúm Dias: %d' % intervalo.num_dias)
        write('\n\tParticipantes | Quota(%) | Quota_Peso(%)')
        total_quota = 0
        total_quota_peso = 0
        for participante in intervalo.participantes:
            quota = intervalo.quota[participante]
            quota_peso = intervalo.quota_peso[participante]
            total_quota += quota
            total_quota_peso += quota_peso
            write('\n\t%14s|%9.2f |%9.2f' % (participante.pessoa.nome, quota, quota_peso))
        write('\n\t%14s|%9.2f |%9.2f\n\n' % (' TOTAL', total_quota, total_quota_peso))
    sys.stdout.flush()
