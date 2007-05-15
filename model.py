# -*- coding: utf-8 -*-

from elixir      import Unicode, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, has_field, using_options, using_table_options, using_mapper_options
from elixir      import has_many as one_to_many
from elixir      import belongs_to as many_to_one
from elixir      import has_and_belongs_to_many as many_to_many
from elixir      import metadata, objectstore
from sqlalchemy  import *
from datetime    import date, datetime, time
import csv
from decimal     import Decimal
from dateutil.relativedelta import relativedelta
from sets import Set

class Pessoa(Entity):
	has_field('nome', Unicode(80), nullable = False, unique = True)
	using_options(tablename = 'pessoa')
	one_to_many('contatos', of_kind = 'Contato', inverse = 'pessoa', order_by = ['tipo', 'contato'])
	
	def get_telefones():
		return Telefone.select(Telefone.c.id_pessoa_resp == self.id)
	
	def get_emails():
		pass
	
	def get_telefones_contato():
		pass









class Contato(Entity):
	has_field('contato', Unicode(100), nullable = False),
	has_field('tipo', Integer, nullable = False),
	many_to_one('pessoa', of_kind = 'Pessoa', inverse = 'contatos', colname = 'id_pessoa',
		column_kwargs = dict(nullable = False))
	using_options(tablename = 'contato')










class Telefone(Entity):
	'''
	Telefone com algum morador sendo responsável.
	
	Não deve haver mais de um morador sendo responsável pelo telefone em uma república, mas esta restrição ainda não está
	firmada no código ou no banco de dados.
	'''
	has_field('numero', Numeric(12, 0), primary_key = True)
	has_field('descricao', Unicode)
	using_options(tablename = 'telefone')
	many_to_one('responsavel', of_kind = 'Morador', colname = 'id_morador', inverse = 'telefones', column_kwargs = dict(primary_key = True))








class Republica(Entity):
	has_field('nome', Unicode(80), nullable = False)
	has_field('data_criacao', Date, default = date.today, nullable = False)
	has_field('proximo_rateio', Date)
	has_field('logradouro', Unicode(150))
	has_field('complemento', Unicode(100))
	has_field('bairro', Unicode(100))
	has_field('cidade', Unicode(80))
	has_field('uf', String(2))
	has_field('cep', String(8))
	using_options(tablename = 'republica')
	one_to_many('fechamentos', of_kind = 'Fechamento', inverse = 'republica', order_by = '-data')
	one_to_many('contas_telefone', of_kind = 'ContaTelefone', inverse = 'republica')
	one_to_many('tipos_despesa', of_kind = 'TipoDespesa', inverse = 'republica')
	
	
	def _proximo_rateio(self):
		if len(self.fechamentos) and ((self.proximo_rateio is None) or (self.proximo_rateio <= self.fechamentos[0].data)):
			self.proximo_rateio = self.fechamentos[0].data + relativedelta(months = 1)
		elif (self.proximo_rateio is None) or (self.proximo_rateio <= self.data_criacao):
			self.proximo_rateio = self.data_criacao + relativedelta(months = 1)
		return self.proximo_rateio
	
	
	def _datas_fechamentos(self):
		'''
		Todas as datas de fechamento em ordem decrescente
		'''
		result = [self._proximo_rateio()]
		result.extend([fechamento.data for fechamento in self.fechamentos])
		result.append(self.data_criacao)
		return result
	
	
	def get_periodo_da_data(self, data_ref):
		'''
		Obtém o período em que a data_ref se encontra
		'''
		data_inicial = None
		data_final   = None
		
		proximo_rateio = self._proximo_rateio()
		if proximo_rateio < data_ref:
			data_inicial = proximo_rateio
			data_final   = data_ref + relativedelta(days = 1)
		elif data_ref < self.data_criacao:
			data_inicial = data_ref
			data_final   = self.data_criacao - relativedelta(days = 1)
		else:
			datas = self._datas_fechamentos()
			for i in range(len(datas) - 1):
				if datas[i] > data_ref >= datas[i + 1]:
					data_final   = datas[i] - relativedelta(days = 1)
					data_inicial = datas[i + 1]
					break
		
		return (data_inicial, data_final)
	
	
	def ultimo_periodo_fechamento(self):
		'''
		Último período de fechamento da república. Caso não haja nenhum, retorna a data em que a república foi criada
		'''
		datas = self._datas_fechamentos()
		if len(datas) > 2:
			return (datas[2], datas[1] - relativedelta(days = 1))
		else:
			return self.proximo_periodo_fechamento()
	
	
	def proximo_periodo_fechamento(self):
		'''
		Último de fechamento até o dia_fechamento do próximo mês
		'''
		datas = self._datas_fechamentos()
		return (datas[1], datas[0] - relativedelta(days = 1))
	
	
	def retifica_periodo(self, data_inicial = None, data_final = None):
		'''
		Se a data inicial é fornecida, determina o período em que ela se encontra, senão, retorna o próximo período de fechamento
		'''
		if data_inicial and not data_final:
			# uma data fornecida. Então deseja o período em que essa data se encontra
			di, df = self.get_periodo_da_data(data_inicial)
			data_inicial = None
		elif not data_inicial:
			# nenhuma data fornecida, obtém o próximo fechamento
			di, df = self.proximo_periodo_fechamento()
		
		if not data_inicial:
			data_inicial = di
		if not data_final:
			data_final = df
		
		# garante que as datas estão em ordem crescente
		if data_inicial > data_final:
			data_inicial, data_final = data_final, data_inicial
		return (data_inicial, data_final)
	
	
	def moradores(self, data_inicial = None, data_final = None):
		'''
		Retorna os moradores da república no período de tempo
		'''
		data_inicial, data_final = self.retifica_periodo(data_inicial, data_final)
		return Morador.select(
					and_(
						Morador.c.id_republica == self.id,
						Morador.c.data_entrada < data_final,
						or_(Morador.c.data_saida >= data_inicial, Morador.c.data_saida == None)
					)
				)
	
	




class MoradorRateio(object):
	'''
	Classe que representa um morador durante o rateio de despesas de telefone _e_ do fechamento das contas do mẽs.
	
	Esta classe tem como objetivo encapsular os dados do morador no fechamento sem bagunçar o objeto morador original.
	'''
	pass







class Fechamento(Entity):
	has_field('data', Date, primary_key = True)
	using_options(tablename = 'fechamento')
	many_to_one('republica', of_kind = 'Republica', inverse = 'fechamentos', colname = 'id_republica',
		column_kwargs = dict(primary_key = True))
	
	
	def executar_rateio(self, data_inicial = None, data_final = None):
		'''
		Calcula a divisão das despesas em determinado período
		'''
		
		self.data_inicial, self.data_final = self.republica.retifica_periodo(self.data - relativedelta(days = 1))
	
		self.totais_despesas                = dict()
		self.totais_despesas['gerais']      = dict()
		self.totais_despesas['especificas'] = dict()
		
		self.rateio     = dict()
		self.total_dias = 0
		
		self.moradores = Set(self.republica.moradores(self.data_inicial, self.data_final))
		self.despesas  = []
		
		# Divisão das contas de telefone
		self.contas_telefone = self.republica.contas_telefone(self.data_inicial, self.data_final)
		for conta_telefone in self.contas_telefone:
			conta_telefone.executar_rateio()
			self.moradores.add(conta_telefone.rateio.keys())
		
		# Contabilização das despesas pagas por cada morador
		for morador in self.moradores:
			rateio[morador].qtd_dias = morador.qtd_dias_morados(self.data_inicial, self.data_final)
			total_dias              += morador.qtd_dias
			rateio[morador].despesas = dict(gerais = Decimal(0), especificas = Decimal(0))
			for despesa in morador.despesas(data_inicial, data_final):
				self.despesas.append(despesa)
				tipo_despesa = despesa.tipo_despesa
				classe       = 'gerais' if not tipo_despesa.especifica else 'especifica'
				morador.total_despesas[classe]       += despesa.valor
				totais_despesas[classe][tipo_despesa] = totais_despesas[classe].get(tipo_despesa, Decimal('0.00')) + despesa.valor
			
		self.total_geral      = sum(totais_despesas['gerais'].values())
		self.total_especifico = sum(totais_despesas['especificas'].values())
		
		
		# Divisão das contas
		for morador in self.moradores:
			morador.quota_geral = total_geral * morador.qtd_dias / total_dias - morador.total_despesas['gerais']
			morador.quota_especifica = Decimal(0)
			for conta_telefone in self.contas_telefone:
				morador.quota_especifica += conta_telefone.rateio[morador]['a_pagar']
			morador.saldo_final = morador.quota_geral + morador.quota_especifica
			
		self._executar_acerto_final()
		
	
	def _executar_acerto_final(self):
		'''
		Executa o acerto final das contas, determinando quem deve pagar o que pra quem. A ordem dos credores
		e devedores é ordenada para que sempre dê a mesma divisão.
		'''
		def compara_saldos(m1, m2):
			dif = self.rateio[m1].saldo_final - self.rateio[m2].saldo_final
			if dif > 0:
				return 1
			elif dif < 0:
				return -1
			else:
				return 0
		
		def compara_nomes(m1, m2):
			nome1 = m1.pessoa.nome
			nome2 = m2.pessoa.nome
			if nome1 > nome2:
				return 1
			elif nome1 < nome2:
				return -1
			else:
				return 0
		
		credores  = Set([morador for morador in self.moradores if self.rateio[morador].saldo_final <= 0])
		devedores = self.moradores - credores
		
		# ordena a lista de credores e devedores de acordo com o saldo_final
		self.moradores = [morador for morador in self.moradores]
		self.moradores.sort(compara_nomes)
		credores  = [credor for credor in credores]
		devedores = [devedor for devedor in devedores]
		credores.sort(compara_saldos)
		devedores.sort(compara_saldos)
		
		self.acerto_a_pagar = dict()
		if len(devedores) == 0: return
		for devedor in devedores:
			self.acerto_a_pagar[devedor] = dict()
		
		devedores = iter(devedores)
		try:
			devedor     = devedores.next()
			saldo_pagar = self.rateio[devedor].saldo_final
			for credor in credores:
				saldo_receber = abs(self.rateio[credor].saldo_final)
				while (saldo_receber > 0):
						if saldo_receber >= saldo_pagar:
							self.acerto_a_pagar[devedor][credor] = saldo_pagar
							saldo_receber -= saldo_pagar
							devedor        = devedores.next()
							saldo_pagar    = self.rateio[devedor].saldo_final
						else:
							self.acerto_a_pagar[devedor][credor] = saldo_receber
							saldo_pagar  -= saldo_receber
							saldo_receber = 0
		except StopIteration:
			return





class ContaTelefone(Entity):
	'''
	Representa cada conta de telefone que chega por mês para a república.
	'''
	# campo id implícito
	has_field('vencimento', Date, nullable = False)
	has_field('emissao', Date, nullable = False)
	has_field('telefone', Numeric(12, 0))
	has_field('companhia', Integer, nullable = False)
	has_field('franquia', Numeric(10,2), default = 0)
	has_field('servicos', Numeric(10,2), default = 0)
	using_options(tablename = 'conta_telefone')
	using_table_options(UniqueConstraint('telefone', 'emissao'))
	many_to_one('republica', of_kind = 'Republica', inverse = 'contas_telefone', colname = 'id_republica',
		column_kwargs = dict(nullable = False))
	one_to_many('telefonemas', of_kind = 'Telefonema', inverse = 'conta_telefone', order_by = 'numero')
	
	def determinar_responsaveis_telefonemas(self):
		'''
		Determina os responsáveis pelos telefonemas da conta
		'''
		responsaveis_telefones = dict(
						select(
								[Telefone.c.numero, Telefone.c.id_morador],
								and_(
									Telefone.c.id_morador == Morador.c.id,
									Morador.c.id_republica == self.id_republica
									)
							).execute().fetchall()
						)
		for telefonema in self.telefonemas:
			if telefonema.responsavel is None and telefonema.numero in responsaveis_telefones:
				telefonema.responsavel = Morador.get_by(Morador.c.id == responsaveis_telefones[telefonema.numero])
		
		objectstore.flush()
	
	
	def interpreta_csv_net_fone(self, linhas):
		# ignora as 3 primeiras linhas de cabeçalho
		linhas = linhas[3:]
		col_numero  = 4
		col_tipo    = 2
		col_duracao = 11
		col_valor   = 13
		telefonemas = dict()
		
		# palavras usadas na descrição que ajudam a classificar o telefonema
		tipos_fone      = ['FIXOS', 'CELULARES', 'NETFONE']
		tipos_distancia = ['LOCAIS', 'DDD', 'DDI'] # confirmar se aparece DDI
		
		# posição das palavras que determinam os tipos dentro da descrição
		col_tipo_fone      = -1
		col_tipo_distancia = 3
		
		for linha in linhas:
			numero  = int(linha[col_numero].strip())
			descr   = linha[col_tipo].split()
			valor   = Decimal(linha[col_valor].strip())
			
			milesimos_minutos = int(linha[col_duracao].strip())
			segundos          = milesimos_minutos * 60 / 1000
			
			tipo_fone      = tipos_fone.index(descr[col_tipo_fone])
			tipo_distancia = tipos_distancia.index(descr[col_tipo_distancia])
			
			if numero not in telefonemas:
				# não consegui fazer contas apenas com time. Foi necessário usar relativedelta
				telefonemas[numero] = [segundos, valor, tipo_fone, tipo_distancia]
			else:
				telefonemas[numero][0] += segundos
				telefonemas[numero][1] += valor
		
		return telefonemas
	
	
	def importar_csv(self, arquivo, tipo):
		'''
		Importa um arquivo .csv referente a uma conta telefônica de uma operadora.
		
		Qualquer telefonema pré-existente no período de referência fornecido é apagado, e o resultado final fica sendo apenas
		o do arquivo importado
		'''
		
		if tipo == 1:
			func_interpreta_csv = self.interpreta_csv_net_fone
		else:
			func_interpreta_csv = None
		
		linhas      = [linha for linha in csv.reader(arquivo)]
		telefonemas = func_interpreta_csv(linhas)
		
		# antes de registrar os novos telefonemas, é necessário apagar os anteriores do mesmo mês
		Telefonema.table.delete(Telefonema.c.id_conta_telefone == self.id).execute()
		
		# registra os novos telefonemas
		for numero, atributos in telefonemas.iteritems():
			Telefonema(
				numero         = numero,
				conta_telefone = self,
				segundos       = atributos[0],
				valor          = atributos[1],
				tipo_fone      = atributos[2],
				tipo_distancia = atributos[3]
			)
		objectstore.flush()
		self.determinar_responsaveis_telefonemas()
	
	
	def executar_rateio(self):
		'''
		Divide a conta de telefone.
		
		Critérios:
		1. Os telefonemas sem dono são debitados da franquia
		2. A franquia restante é dividida entre os moradores de acordo com o número de dias morados por cada um
		3. Os serviços (se houverem) também são divididos de acordo com o número de dias morados
		4. O valor excedente é quanto cada morador gastou além da franquia a que tinha direito
		5. O valor excedente que cada morador deve pagar pode ser compensado pelo faltante de outro morador em atingir sua franquia
		'''
		periodo = self.republica.get_periodo_da_data(self.emissao)
		rateio = dict()
		
		total_dias = 0
		# determina os moradores atuais da república
		for morador in self.republica.moradores(periodo[0], periodo[1]):
			qtd_dias    = morador.qtd_dias_morados(periodo[0], periodo[1])
			total_dias += qtd_dias
			rateio[morador]          = MoradorRateio()
			rateio[morador].qtd_dias = Decimal(qtd_dias) # Decimal pois vai ser usado em outras contas depois
			rateio[morador].gastos   = Decimal(0)
		
		# Cálculo dos telefonemas de acordo com o responsável: morador, ex-morador ou sem dono
		total_sem_dono     = Decimal(0)
		total_ex_moradores = Decimal(0)
		total_telefonemas  = Decimal(0)
		for telefonema in self.telefonemas:
			valor = telefonema.valor if type(telefonema.valor) is Decimal else str(telefonema.valor)
			
			total_telefonemas += valor
			morador = telefonema.responsavel
			if morador:
				if morador not in rateio:
					# ex-morador que tem telefonema pendente
					rateio[morador]          = MoradorRateio()
					rateio[morador].qtd_dias = Decimal(0)
					rateio[morador].gastos   = Decimal(0)
					total_ex_moradores += telefonema.valor
				
				rateio[morador].gastos += valor
			else:
				total_sem_dono += telefonema.valor
		
		# determina a franquia e o excedente de cada morador
		total_excedente = 0
		for morador in rateio.values():
			franquia_morador = (self.franquia * morador.qtd_dias) / total_dias
			div_tel_sem_dono = (total_sem_dono * morador.qtd_dias) / total_dias
			excedente        = morador.gastos + div_tel_sem_dono - franquia_morador
			excedente        = excedente if excedente > 0 else Decimal(0)
			total_excedente += excedente
			
			morador.franquia  = franquia_morador
			morador.sem_dono  = div_tel_sem_dono
			morador.excedente = excedente
			morador.servicos  = (self.servicos * morador.qtd_dias) / total_dias
		
		total_conta = self.servicos + (total_telefonemas if total_telefonemas > self.franquia else self.franquia)
		if total_excedente > 0:
			excedente_conta = total_conta - self.franquia
		else:
			excedente_conta = 0
			total_excedente = 1
		
		# só agora é possível determinar quanto cada um paga
		for morador in rateio.values():
			morador.a_pagar = morador.franquia + \
								morador.servicos + \
								(morador.excedente * excedente_conta) / total_excedente
		
		resumo = dict()
		resumo['total_telefonemas']  = total_telefonemas
		resumo['total_conta']        = total_conta
		resumo['total_dias']         = total_dias
		resumo['total_sem_dono']     = total_sem_dono
		resumo['total_ex_moradores'] = total_ex_moradores
		
		self.resumo = resumo
		self.rateio = rateio
		
		return (resumo, rateio)


class Telefonema(Entity):
	has_field('numero',         Numeric(12, 0), primary_key = True)
	has_field('tipo_fone',      Integer,        nullable = False)	# fixo, celular, net fone
	has_field('tipo_distancia', Integer,        nullable = False)	# Local, DDD, DDI
	has_field('segundos',       Integer,        nullable = False)
	has_field('valor',          Numeric(10, 2), nullable = False)
	many_to_one('responsavel',    of_kind = 'Morador',       colname = 'id_morador')
	many_to_one('conta_telefone', of_kind = 'ContaTelefone', colname = 'id_conta_telefone', inverse = 'telefonemas', column_kwargs = dict(primary_key = True))
	using_options(tablename = 'telefonema')


class Morador(Entity):
	has_field('data_entrada', Date, default = date.today, nullable = False)
	has_field('data_saida', Date)
	many_to_one('republica', of_kind = 'Republica', colname = 'id_republica', column_kwargs = dict(nullable = False))
	many_to_one('pessoa', of_kind = 'Pessoa', colname = 'id_pessoa', column_kwargs = dict(nullable = False))
	one_to_many('telefones', of_kind = 'Telefone', inverse = 'responsavel')
	using_options(tablename = 'morador')
	# UniqueConstraint ainda não funciona nessa versão do elixir. Veja http://groups.google.com/group/sqlelixir/browse_thread/thread/46a2733c894e510b/048cde52cd6afa35?lnk=gst&q=UniqueConstraint&rnum=3#048cde52cd6afa35
	#using_table_options(UniqueConstraint('id_pessoa', 'id_republica', 'data_entrada'))
	
	
	def despesas(self, data_inicial = None, data_final = None):
		data_inicial, data_final = self.republica.retifica_periodo(data_inicial, data_final)
		return Despesa.select(
					and_(
						Despesa.c.id_morador == self.id,
						Despesa.c.data       >= data_inicial,
						Despesa.c.data       <= data_final
						),
					order_by = Despesa.c.data
					)
	
	
	def total_despesas(self, data_inicial = None, data_final = None):
		data_inicial, data_final = self.republica.retifica_periodo(data_inicial, data_final)
		
		def total(especifica):
			return select(
				[func.coalesce(func.sum(Despesa.c.valor), 0)],
				and_(
					Despesa.c.id_morador == self.id,
					Despesa.c.data >= data_inicial,
					Despesa.c.data <= data_final,
					Despesa.c.id_tipo_despesa == TipoDespesa.c.id,
					TipoDespesa.c.especifica == especifica,
					)
				).execute().fetchone()[0]
				
		return (total(especifica = False), total(especifica = True))
	
	
	def despesas_por_tipo(self, tipo_despesa, data_inicial = None, data_final = None):
		return [despesa for despesa in self.despesas(data_inicial, data_final) if despesa.tipo_despesa == tipo_despesa]
	
	
	def telefonemas(self, conta_telefone):
		if conta_telefone.republica is not self.republica:
			return None
		return Telefonema.select(
					and_(
						Telefonema.c.id_conta_telefone == conta_telefone.id,
						Telefonema.c.id_morador == self.id
						),
					order_by = Telefonema.c.numero
					)
	
	
	def qtd_dias_morados(self, data_inicial = None, data_final = None):
		data_inicial, data_final = self.republica.retifica_periodo(data_inicial, data_final)
		entrada = max(self.data_entrada, data_inicial)
		if not self.data_saida:
 			saida = data_final
		else:
			saida = min(self.data_saida, data_final)
		
		qtd_dias = (saida - entrada).days + 1
		return (qtd_dias if qtd_dias >= 0 else 0)






class TipoDespesa(Entity):
	has_field('nome', Unicode(40), nullable = False)
	has_field('especifica', Boolean, default = False)
	has_field('descricao', String)
	using_options(tablename = 'tipo_despesa')
	many_to_one('republica', of_kind = 'Republica', inverse = 'tipo_despesas', column_kwargs = dict(nullable = False))


class Despesa(Entity):
	has_field('data', Date, default = date.today, nullable = False)
	has_field('valor', Numeric(10, 2), nullable = False)
	using_options(tablename = 'despesa')
	many_to_one('responsavel',  of_kind = 'Morador',     colname = 'id_morador',      column_kwargs = dict(nullable = False))
	many_to_one('tipo_despesa', of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))



class DespesaRepetitiva(Entity):
	has_field('dia_vencimento', Integer, nullable = False)
	has_field('valor', Numeric(10,2), nullable = False)
	many_to_one('responsavel',  of_kind = 'Morador', colname = 'id_morador', column_kwargs = dict(nullable = False))
	many_to_one('tipo_despesa', of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))

