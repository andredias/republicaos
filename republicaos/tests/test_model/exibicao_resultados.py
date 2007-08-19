#!/usr/bin/python
# -*- coding: utf-8 -*-

from decimal import Decimal
from pronus_utils import pretty_decimal
import sys
import codecs

(e,d,sr,sw) = codecs.lookup('utf-8')
unicode_to_utf8 = sw(sys.stdout)
write = unicode_to_utf8.write

def print_rateio_conta_telefone(resumo, rateio):
	write('\n\nRATEIO CONTA DE TELEFONE\n------------------------')
	for key, value in resumo.items():
		write('\n%s = %s' % (key, pretty_decimal(value)))
	
	moradores = [(key.pessoa.nome, key) for key in rateio.keys()]
	moradores.sort()
	campos = ('qtd_dias', 'franquia', 'gastos', 'sem_dono', 'excedente', 'servicos', 'a_pagar')
	totais = dict([campo, 0] for campo in campos)
	write('\n\n----------|%9s|%9s|%9s|%9s|%9s|%9s|%9s' % campos)
	for nome, morador in moradores:
		write('\n%10s' % nome)
		for campo in campos:
			format_string = '|%9.2f' if campo != 'qtd_dias' else '|%9s'
			write(format_string % rateio[morador].__dict__[campo])
			totais[campo] += rateio[morador].__dict__[campo]
	
	# mostra totais
	write('\n----------')
	for campo in campos:
		format_string = '|%9.2f' if campo != 'qtd_dias' else '|%9s'
		write(format_string % totais[campo])
	write('\n\n')
	sys.stdout.flush()


def print_resumo_despesas(fechamento):
	write('\n\nRESUMO DAS DESPESAS\n-------------------\nTipo           |  Total')
	tipos_despesa = sorted(fechamento.total_tipo_despesa.keys(), key = lambda obj: obj.nome)
	for tipo_despesa in tipos_despesa:
		write(u'\n%15s| %.2f' % (tipo_despesa.nome, fechamento.total_tipo_despesa[tipo_despesa]))
	write('\n\n%*s = %*s' % (19, 'Total Geral', 7, pretty_decimal(fechamento.total_despesas)))
	write(u'\n%*s = %*d' % (19, u'Número de moradores', 4, len(fechamento.participantes)))
	write(u'\n%*s = %*.2f' % (19, u'Média', 7, \
		(fechamento.total_despesas / (len(fechamento.participantes) if len(fechamento.participantes) else 1))))


def print_despesas(fechamento):
	write(u'\n\nRELAÇÃO DE DESPESAS\n-------------------\n')
	write(u'| %-*s| %-*s| %-*s| %s' % (11, 'Data', 9, 'Valor', 15, 'Tipo Despesa', u'Responsável'))
	for despesa in fechamento.despesas:
		write('\n| %s | %*.2f | %-*s| %s' % (despesa.data, 8, despesa.quantia, 15, despesa.tipo.nome, despesa.responsavel.pessoa.nome))
	write('\n')


def print_rateio(fechamento):
	write(u'\n\nRATEIO\n------\n')
	write(u' %-*s| %-*s| %-*s| %-*s| %-*s| %-*s| %s' %
		(
		9, 'Morador',
		4, 'Dias',
		12, u'Participação',
		8, 'Quota',
		8, 'Telefone',
		8, 'Despesas',
		'Saldo Final'
		)
	)
	for participante in fechamento.participantes:
		rateio_participante = fechamento.rateio[participante]
		write('\n %*s| %*s%%| %*s| %*s| %*s| %*s' % \
			(9, participante.pessoa.nome,
			11, pretty_decimal(fechamento.quota(participante), 1),
			8, pretty_decimal(rateio_participante.quota),
			8, pretty_decimal(rateio_participante.quota_telefone),
			8, pretty_decimal(rateio_participante.total_despesas),
			8, pretty_decimal(rateio_participante.saldo_final)))
		
	total_porcentagem = sum(fechamento.quota(participante) for participante in fechamento.participantes)
	total_quotas      = sum(fechamento.rateio[participante].quota       for participante in fechamento.participantes)
	total_saldo_final = sum(fechamento.rateio[participante].saldo_final for participante in fechamento.participantes)
	write('\n %*s| %*s%%| %*s| %*s| %*s| %*s' % 
		(
		9, 'TOTAL  ',
		11, pretty_decimal(total_porcentagem, 1),
		8, pretty_decimal(total_quotas),
		8, pretty_decimal(fechamento.total_telefone),
		8, pretty_decimal(fechamento.total_despesas),
		8, pretty_decimal(total_saldo_final)
		)
	)
	write('\n\n')


def print_acerto_final(fechamento):
	write('\nACERTO DAS CONTAS\n-----------------')
	write('\n%10s' % ' ')
	for morador in fechamento.participantes:
		write('|%10s' % morador.pessoa.nome)
	write('| Total a Pagar')
	
	for devedor in fechamento.participantes:
		write('\n%10s' % devedor.pessoa.nome)
		total_a_pagar = Decimal(0)
		if devedor not in fechamento.acerto_a_pagar:
			write(('|%10s' % ' ') * (len(fechamento.participantes) + 1))
		else:
			for credor in fechamento.participantes:
				if credor in fechamento.acerto_a_pagar[devedor]:
					a_pagar           = fechamento.acerto_a_pagar[devedor][credor]
					total_a_pagar    += a_pagar
					write('|%10s' % a_pagar)
				else:
					write('|%10s' % ' ')
			write('|%10s' % total_a_pagar)
	write('\n%s' % ('-' * 10 * (len(fechamento.participantes) + 3)))
	write('\n   Receber')
	for credor in fechamento.participantes:
		if credor in fechamento.acerto_a_receber:
			write('|%10s' % sum(fechamento.acerto_a_receber[credor].values()))
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
	write(u'\n\nCÁLCULO DAS QUOTAS DO FECHAMENTO\n-----------------')
	write('\nData Inicial: %s | Data Final: %s' % (fechamento.data_inicial.strftime('%d/%m/%Y'), fechamento.data_final.strftime('%d/%m/%Y')))
	write('\nTotal de dias: %d' % fechamento.total_dias)
	write(u'\nParticipantes | Peso(%) | Quota(%) | Quota_Peso(%)')
	total_peso       = 0
	total_quota      = 0
	total_quota_peso = 0
	for participante in fechamento.participantes:
		peso       = participante.peso_quota(fechamento.data_inicial)
		quota      = fechamento.quota(participante)
		quota_peso = fechamento.quota_peso(participante)
		total_peso       += peso
		total_quota      += quota
		total_quota_peso += quota_peso
		write('\n%14s|%9.2f|%9.2f |%9.2f' % (participante.pessoa.nome, participante.peso_quota(fechamento.data_inicial), quota, quota_peso))
	write('\n%14s|%9.2f|%9.2f |%9.2f\n\n' % (' TOTAL', total_peso, total_quota, total_quota_peso))
	write('\n\nIntervalos:')
	for intervalo in fechamento.intervalos:
		write('\n\t--------------')
		write('\n\tData Inicial: %s | Data Final: %s' % (intervalo.data_inicial.strftime('%d/%m/%Y'), intervalo.data_final.strftime('%d/%m/%Y')))
		write(u'\n\tNúm Dias: %d' % intervalo.num_dias)
		write(u'\n\tParticipantes | Quota(%) | Quota_Peso(%)')
		total_quota      = 0
		total_quota_peso = 0
		for participante in intervalo.participantes:
			quota      = intervalo.quota(participante)
			quota_peso = intervalo.quota_peso(participante)
			total_quota      += quota
			total_quota_peso += quota_peso
			write('\n\t%14s|%9.2f |%9.2f' % (participante.pessoa.nome, quota, quota_peso))
		write('\n\t%14s|%9.2f |%9.2f\n\n' % (' TOTAL', total_quota, total_quota_peso))
	sys.stdout.flush()
			
			
		
