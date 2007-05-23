#!/usr/bin/python
# -*- coding: utf-8 -*-

from decimal import Decimal
import sys
import codecs

(e,d,sr,sw) = codecs.lookup('utf-8')
unicode_to_utf8 = sw(sys.stdout)
write = unicode_to_utf8.write

def print_rateio_conta_telefone(resumo, rateio):
	write('\n\nRATEIO CONTA DE TELEFONE\n------------------------')
	for key, value in resumo.items():
		write('\n%s = %s' % (key, value))
	
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
		write('|%9s' % totais[campo])
	write('\n\n')
	sys.stdout.flush()


def print_resumo_despesas(fechamento):
	write('\n\nRESUMO DAS DESPESAS\n-------------------\nGerais:\n-------\nTipo           |  Total')
	tipos_despesa = [t for t in fechamento.despesas_tipo.keys() if not t.especifica]
	tipos_despesa.sort(key = lambda obj: obj.nome)
	for tipo_despesa in tipos_despesa:
		write(u'\n%15s| %.2f' % (tipo_despesa.nome, fechamento.despesas_tipo[tipo_despesa]))
	write('\n\n%*s = %*.2f' % (19, 'Total Geral', 7, fechamento.total_despesas_gerais))
	write(u'\n%*s = %*d' % (19, u'Número de moradores', 4, len(fechamento.moradores)))
	write(u'\n%*s = %*.2f' % (19, u'Média', 7, \
		(fechamento.total_despesas_gerais / (len(fechamento.moradores) if len(fechamento.moradores) else 1))))
	
	write(u'\n\nEspecíficas:\n------------\nTipo           |  Total')
	tipos_despesa = [t for t in fechamento.despesas_tipo.keys() if t.especifica]
	tipos_despesa.sort(key = lambda obj: obj.nome)
	for tipo_despesa in tipos_despesa:
		write('\n%15s| %.2f' % (tipo_despesa.nome, fechamento.despesas_tipo[tipo_despesa]))
	write(u'\n\nTotal Específico = %s' % fechamento.total_despesas_especificas)


def print_despesas(fechamento):
	write(u'\n\nRELAÇÃO DE DESPESAS\n-------------------\n')
	write(u'| %-*s| %-*s| %-*s| %s' % (11, 'Data', 9, 'Valor', 15, 'Tipo Despesa', u'Responsável'))
	fechamento.despesas.sort(key = lambda obj:obj.data)
	for despesa in fechamento.despesas:
		write('\n| %s | %*.2f | %-*s| %s' % (despesa.data, 8, despesa.valor, 15, despesa.tipo.nome, despesa.responsavel.pessoa.nome))
	write('\n')


def print_rateio_geral(fechamento):
	write(u'\n\nRATEIO DESPESAS GERAIS\n----------------------\n')
	write(u' %-*s| %-*s| %-*s| %-*s| %s' % (9, 'Morador', 4, 'Dias', 8, 'Despesas', 8, 'Quota', 'Saldo Final'))
	for morador in fechamento.moradores:
		rateio_morador = fechamento.rateio[morador]
		write('\n %*s| %*d| %*.2f| %*.2f| %*.2f' % \
			(9, morador.pessoa.nome,
			4, rateio_morador.qtd_dias,
			8, rateio_morador.total_despesas_gerais,
			8, rateio_morador.quota_geral,
			8, rateio_morador.saldo_final_geral))
		
	rateio = fechamento.rateio.values()
	total_dias        = sum(rateio_morador.qtd_dias for rateio_morador in rateio)
	total_despesas    = sum(rateio_morador.total_despesas_gerais for rateio_morador in rateio)
	total_quotas      = sum(rateio_morador.quota_geral for rateio_morador in rateio)
	total_saldo_final = sum(rateio_morador.saldo_final_geral for rateio_morador in rateio)
	write('\n %*s| %*d| %*.2f| %*.2f| %*.2f' % (9, 'TOTAL  ', 4, total_dias, 8, total_despesas, 8, total_quotas, 8, total_saldo_final))
	write('\n\n')


def print_rateio_especifico(fechamento):
	write(u'\n\nRATEIO DESPESAS ESPECÍFICAS\n---------------------------\n')
	write(u' %-*s| %-*s| %-*s| %s' % (9, 'Morador', 8, 'Despesas', 8, 'Quota', 'Saldo Final'))
	for morador in fechamento.participantes:
		rateio_morador = fechamento.rateio[morador]
		write('\n %*s| %*.2f| %*.2f| %*.2f' % \
			(9, morador.pessoa.nome,
			8, rateio_morador.total_despesas_especificas,
			8, rateio_morador.quota_especifica,
			8, rateio_morador.saldo_final_especifico))
	
	rateio = fechamento.rateio.values()
	total_despesas    = sum(rateio_morador.total_despesas_especificas for rateio_morador in rateio)
	total_quotas      = sum(rateio_morador.quota_especifica for rateio_morador in rateio)
	total_saldo_final = sum(rateio_morador.saldo_final_especifico for rateio_morador in rateio)
	write('\n %*s| %*.2f| %*.2f| %*.2f' % (9, 'TOTAL  ', 8, total_despesas, 8, total_quotas, 8, total_saldo_final))
	write('\n\n')


def print_rateio_final(fechamento):
	write(u'\n\nRATEIO FINAL\n------------\n')
	write(u' %-*s| %-*s| %-*s| %s' % (9, 'Morador', 8, 'Geral', 10, u'Específico', 'Saldo Final'))
	for morador in fechamento.participantes:
		rateio_morador = fechamento.rateio[morador]
		write('\n %*s| %*.2f| %*.2f| %*.2f' % \
			(9, morador.pessoa.nome,
			8, rateio_morador.saldo_final_geral,
			10, rateio_morador.saldo_final_especifico,
			8, rateio_morador.saldo_final))
	rateio = fechamento.rateio.values()
	total_geral       = sum(rateio_morador.saldo_final_geral for rateio_morador in rateio)
	total_especifico  = sum(rateio_morador.saldo_final_especifico for rateio_morador in rateio)
	total_saldo_final = sum(rateio_morador.saldo_final for rateio_morador in rateio)
	write('\n %*s| %*.2f| %*.2f| %*.2f' % (9, 'TOTAL  ', 8, total_geral, 10, total_especifico, 8, total_saldo_final))
	write('\n\n')


def print_acerto_final(fechamento):
	write('\nACERTO DAS CONTAS\n-----------------')
	write('\n%10s' % ' ')
	for morador in fechamento.participantes:
		write('|%10s' % morador.pessoa.nome)
	write('| Total a Pagar')
	
	a_receber = dict()
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
					a_receber[credor] = a_receber.get(credor, Decimal(0)) + a_pagar
					write('|%10s' % a_pagar)
				else:
					write('|%10s' % ' ')
			write('|%10s' % total_a_pagar)
	write('\n%s' % ('-' * 10 * (len(fechamento.participantes) + 3)))
	write('\n   Receber')
	for credor in fechamento.participantes:
		if credor in a_receber:
			write('|%10s' % a_receber[credor])
		else:
			write('|%10s' % ' ')
	write('\n\n\n')



def print_fechamento(fechamento):
	write('=' * 50)
	print_resumo_despesas(fechamento)
	print_despesas(fechamento)
	print_rateio_geral(fechamento)
	print_rateio_especifico(fechamento)
	print_rateio_final(fechamento)
	print_acerto_final(fechamento)
	sys.stdout.flush()