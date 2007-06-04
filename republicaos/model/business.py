# -*- coding: utf-8 -*-

from elixir      import Unicode, Boolean, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, has_field, using_options, using_table_options, using_mapper_options
from elixir      import has_many as one_to_many
from elixir      import belongs_to as many_to_one
from elixir      import has_and_belongs_to_many as many_to_many
from sqlalchemy  import types, and_, or_, select, UniqueConstraint
from datetime    import date, datetime, time
import csv
from decimal     import Decimal
from dateutil.relativedelta import relativedelta

from turbogears.database import metadata



class Money(types.TypeEngine):
	'''
	Classe para poder usar o Decimal com o SQLite e outros BD além do Postgres
	'''
	def __init__(self, precision=10, length=2):
		self.precision = precision
		self.length = length

	def get_col_spec(self):
		return 'NUMERIC (%(precision)s, %(length)s)' % {'precision': self.precision, 'length' : self.length}

	def convert_bind_param(self, value, dialect):
		return str(value)

	def convert_result_value(self, value, dialect):
		if type(value) is float:
			value = str(value)
		return Decimal(value)




class ModelIntegrityException(Exception):
	pass


class Pessoa(Entity):
	has_field('nome', Unicode(80), nullable = False, unique = True)
	using_options(tablename = 'pessoa')
	one_to_many('contatos', of_kind = 'Contato', inverse = 'pessoa', order_by = ['tipo', 'contato'])
	
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










class TelefoneRegistrado(Entity):
	'''
	TelefoneRegistrado registrado na república tendo algum morador como responsável.
	
	Não poderá haver mais de um morador sendo responsável pelo telefone em uma república. Essa restrição
	é reforçada pela chave primária.
	'''
	has_field('numero', Numeric(12, 0), primary_key = True)
	has_field('descricao', Unicode)
	using_options(tablename = 'telefone')
	many_to_one(
			'republica',
			of_kind = 'Republica',
			colname = 'id_republica',
			inverse = 'telefones_registrados',
			column_kwargs = dict(primary_key = True)
			)
	many_to_one('responsavel', of_kind = 'Morador', colname = 'id_morador', inverse = 'telefones', column_kwargs = dict(nullable = False))
	
	def __repr__(self):
		return "<número: %d, republica: '%s', responsável: '%s'>" % (self.numero, self.republica.nome, self.responsavel.pessoa.nome)







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
	one_to_many('tipos_despesa', of_kind = 'TipoDespesa', inverse = 'republica', order_by = 'nome')
	one_to_many('telefones_registrados', of_kind = 'TelefoneRegistrado', inverse = 'republica', order_by = 'numero')
	
	
	def datas_fechamento(self):
		'''
		Todas as datas de fechamento em ordem decrescente
		'''
		result = [fechamento.data for fechamento in self.fechamentos]
		result.append(self.data_criacao)
		return result
	
	
	@property
	def proxima_data_fechamento(self):
		datas_fechamento = self.datas_fechamento()
		if (not self.proximo_rateio) or (self.proximo_rateio <= datas_fechamento[0]):
			self.proximo_rateio = datas_fechamento[0] + relativedelta(months = 1)
		return self.proximo_rateio
	
	
	def periodo_fechamento(self, data_ref = None):
		'''
		Obtém o período em que a data_ref se encontra
		'''
		datas_fechamento = [self.proxima_data_fechamento] + self.datas_fechamento()
		if (not data_ref) or (data_ref > datas_fechamento[0]):
			data_ref = datas_fechamento[0]
		elif data_ref < datas_fechamento[-1]:
			data_ref = datas_fechamento[-1]
			
		for i in range(len(datas_fechamento) - 1):
			if datas_fechamento[i] >= data_ref >= datas_fechamento[i + 1]:
				data_final   = datas_fechamento[i] - relativedelta(days = 1)
				data_inicial = datas_fechamento[i + 1]
				break
		
		return (data_inicial, data_final)
	
	
	def moradores(self, data_inicial, data_final):
		'''
		Retorna os moradores da república no período de tempo
		'''
		return Morador.select(
					and_(
						Morador.c.id_republica == self.id,
						Morador.c.data_entrada < data_final,
						or_(Morador.c.data_saida >= data_inicial, Morador.c.data_saida == None)
					)
				)
	
	
	def contas_telefone(self, data_inicial, data_final):
		'''
		Retorna as contas de telefone da república no período
		'''
		return ContaTelefone.select(
					and_(
						ContaTelefone.c.id_republica == self.id,
						ContaTelefone.c.emissao >= data_inicial,
						ContaTelefone.c.emissao <= data_final
					)
				)
	
	
	def registrar_responsavel_telefone(self, numero, responsavel = None, descricao = None):
		telefone = None
		for tr in self.telefones_registrados:
			if numero == tr.numero:
				telefone = tr
				break
		
		if responsavel:
			assert responsavel.republica == self
		
		if telefone and responsavel:
			telefone.responsavel = responsavel
			telefone.descricao   = descricao
			telefone.flush()
		elif not telefone and responsavel:
			registro = TelefoneRegistrado(numero = numero, republica = self, responsavel = responsavel, descricao = descricao)
			registro.flush()
			# não tenho certeza se a adição à lista da república deveria acontecer automaticamente.
			# veja o post publicado no grupo do sqlelixir:
			# http://groups.google.com/group/sqlelixir/browse_thread/thread/710e82c3ad586aab/03fc48b416a09fcf#03fc48b416a09fcf
			self.telefones_registrados.append(registro)
		elif telefone and not responsavel: # não há mais responsável
			telefone.delete()
			telefone.flush()
		# else: o telefone não está registrado e não tem reponsável -> nada a fazer
		
		return
	
	




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
	
	
	def executar_rateio(self):
		'''
		Calcula a divisão das despesas em determinado período
		'''
		self.data_inicial, self.data_final = self.republica.periodo_fechamento(self.data)
		
		self.total_despesas_gerais      = Decimal(0)
		self.total_despesas_especificas = Decimal(0)
		self.total_dias                 = 0
		
		self.moradores     = set(self.republica.moradores(self.data_inicial, self.data_final))
		self.ex_moradores  = set()
		self.despesas      = []
		self.despesas_tipo = dict()
		self.rateio        = dict()
		
		# Divisão das contas de telefone
		self.contas_telefone = self.republica.contas_telefone(self.data_inicial, self.data_final)
		for conta_telefone in self.contas_telefone:
			conta_telefone.executar_rateio()
			self.ex_moradores.update(set(conta_telefone.rateio.keys()) - self.moradores)
		
		# Contabilização das despesas pagas por cada morador
		for morador in (self.moradores | self.ex_moradores):
			self.rateio[morador] = MoradorRateio()
			rateio_morador = self.rateio[morador]
			rateio_morador.qtd_dias = morador.qtd_dias_morados(self.data_inicial, self.data_final)
			self.total_dias        += rateio_morador.qtd_dias
			rateio_morador.total_despesas_gerais      = Decimal(0)
			rateio_morador.total_despesas_especificas = Decimal(0)
			
			for despesa in morador.despesas(self.data_inicial, self.data_final):
				self.despesas.append(despesa)
				if not despesa.tipo.especifica:
					rateio_morador.total_despesas_gerais += despesa.quantia
					self.total_despesas_gerais           += despesa.quantia
				else:
					rateio_morador.total_despesas_especificas += despesa.quantia
					self.total_despesas_especificas           += despesa.quantia
				self.despesas_tipo[despesa.tipo] = self.despesas_tipo.get(despesa.tipo, Decimal('0.00')) + despesa.quantia
				
			# contas específicas por enquanto, só de telefone
			rateio_morador.quota_especifica = Decimal(0)
			for conta_telefone in self.contas_telefone:
				if morador in conta_telefone.rateio:
					rateio_morador.quota_especifica += conta_telefone.rateio[morador].a_pagar
			rateio_morador.saldo_final_especifico = rateio_morador.quota_especifica - rateio_morador.total_despesas_especificas
			
		# Divisão das contas
		for rateio_morador in self.rateio.values():
			rateio_morador.quota_geral       = self.total_despesas_gerais * rateio_morador.qtd_dias / self.total_dias
			rateio_morador.saldo_final_geral = rateio_morador.quota_geral - rateio_morador.total_despesas_gerais
			rateio_morador.saldo_final       = rateio_morador.saldo_final_geral + rateio_morador.saldo_final_especifico
		
			
		# transforma set em list e ordena por nome
		self.moradores    = list(self.moradores)
		self.ex_moradores = list(self.ex_moradores)
		self.participantes = self.moradores + self.ex_moradores
		self.moradores.sort(key = lambda obj:obj.pessoa.nome)
		self.ex_moradores.sort(key = lambda obj:obj.pessoa.nome)
		self.participantes.sort(key = lambda obj:obj.pessoa.nome)
		
		self._executar_acerto_final()
	
	
	def _executar_acerto_final(self):
		'''
		Executa o acerto final das contas, determinando quem deve pagar o que pra quem. A ordem dos credores
		e devedores é ordenada para que sempre dê a mesma divisão.
		'''
		credores  = [morador for morador in self.participantes if self.rateio[morador].saldo_final <= 0]
		devedores = list(set(self.participantes) - set(credores))
		
		# ordena a lista de credores e devedores de acordo com o saldo_final
		credores.sort(key =  lambda obj:self.rateio[obj].saldo_final)
		devedores.sort(key = lambda obj:self.rateio[obj].saldo_final)
		
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
	
	
	#
	# Funções a seguir deveriam já estar habilitadas no Elixir para funcionar como os triggers do Banco de Dados
	#
	def before_insert(self):
		if self.data > self.republica.fechamentos[0].data:
			raise ModelIntegrityException(message = 'Não é permitido lançar fechamento atrasado')
	
	
	def after_insert(self):
		self.republica.proximo_rateio = self.data + relativedelta(months = 1)
		self.republica.flush()





class ContaTelefone(Entity):
	'''
	Representa cada conta de telefone que chega por mês para a república.
	'''
	# campo id implícito
	has_field('vencimento', Date, nullable = False)
	has_field('emissao', Date, nullable = False)
	has_field('telefone', Numeric(12, 0))
	has_field('id_operadora', Integer, nullable = False)
	has_field('franquia', Money(10,2), default = 0)
	has_field('servicos', Money(10,2), default = 0)
	using_options(tablename = 'conta_telefone')
	using_table_options(UniqueConstraint('telefone', 'emissao'))
	many_to_one('republica', of_kind = 'Republica', inverse = 'contas_telefone', colname = 'id_republica',
		column_kwargs = dict(nullable = False))
	one_to_many('telefonemas', of_kind = 'Telefonema', order_by = 'numero')
	
	def determinar_responsaveis_telefonemas(self):
		'''
		Determina os responsáveis pelos telefonemas da conta
		'''
		numeros_registrados = dict([(tr.numero, tr) for tr in self.republica.telefones_registrados])
		for telefonema in self.telefonemas:
			if telefonema.responsavel is None and telefonema.numero in numeros_registrados:
				telefonema.responsavel = numeros_registrados[telefonema.numero].responsavel
				telefonema.flush()
		return
	
	
	def _interpreta_csv_net_fone(self, linhas):
		# ignora as 3 primeiras linhas de cabeçalho
		linhas        = linhas[3:]
		col_numero    = 4
		col_descricao = 2
		col_duracao   = 11
		col_quantia   = 13
		telefonemas   = dict()
		
		# palavras usadas na descrição que ajudam a classificar o telefonema
		tipos_fone      = ['FIXO', 'CELULAR', 'NETFONE']
		tipos_distancia = ['LOCA', 'DDD', 'DDI'] # confirmar se aparece DDI
		
		encargos = Decimal(0)
		
		for linha in linhas:
			quantia   = Decimal(linha[col_quantia].strip())
			descricao = linha[col_descricao].strip()
			try:
				numero = int(linha[col_numero].strip())
				
				milesimos_minutos = int(linha[col_duracao].strip())
				segundos          = milesimos_minutos * 60 / 1000
				
				# determina o tipo de telefone
				for tipo in tipos_fone:
					if tipo in descricao:
						tipo_fone = tipos_fone.index(tipo)
						break
				
				# determina o tipo de ligação
				for tipo in tipos_distancia:
					if tipo in descricao:
						tipo_distancia = tipos_distancia.index(tipo)
						break
				
				if numero not in telefonemas:
					# não consegui fazer contas apenas com time. Foi necessário usar relativedelta
					telefonemas[numero] = dict(
											segundos       = segundos,
											quantia        = quantia,
											tipo_fone      = tipo_fone,
											tipo_distancia = tipo_distancia
											)
				else:
					telefonemas[numero]['segundos'] += segundos
					telefonemas[numero]['quantia']  += quantia
			except ValueError:
				# quando é alguma multa ou ajuste, não aparece um número válido de telefone, o que gera uma exceção
				if 'FRANQUIA' not in descricao:
					encargos += quantia
		
		return (telefonemas, encargos)
	
	
	def importar_csv(self, arquivo):
		'''
		Importa um arquivo .csv referente a uma conta telefônica de uma operadora.
		
		Qualquer telefonema pré-existente no período de referência fornecido é apagado, e o resultado final fica sendo apenas
		o do arquivo importado
		'''
		
		if self.id_operadora == 1:
			func_interpreta_csv = self._interpreta_csv_net_fone
		else:
			func_interpreta_csv = None
		
		#arquivo precisa ser uma lista de linhas
		if type(arquivo) is str:
			arquivo = arquivo.strip().splitlines()
			
		linhas = [linha for linha in csv.reader(arquivo)]
		telefonemas, encargos = func_interpreta_csv(linhas)
		
		if encargos > 0:
			if not self.servicos:
				self.servicos = encargos
			else:
				self.servicos += encargos
			self.flush()
		
		# antes de registrar os novos telefonemas, é necessário apagar os anteriores do mesmo mês
		Telefonema.table.delete(Telefonema.c.id_conta_telefone == self.id).execute()
		
		# registra os novos telefonemas
		for numero, atributos in telefonemas.iteritems():
			Telefonema(
				numero         = numero,
				conta_telefone = self,
				segundos       = atributos['segundos'],
				quantia        = atributos['quantia'],
				tipo_fone      = atributos['tipo_fone'],
				tipo_distancia = atributos['tipo_distancia']
			).flush()
		self.determinar_responsaveis_telefonemas()
	
	
	def executar_rateio(self):
		'''
		Divide a conta de telefone.
		
		Critérios:
		1. Os telefonemas sem dono são debitados da franquia
		2. A franquia restante é dividida entre os moradores de acordo com o número de dias morados por cada um
		3. Os serviços (se houverem) também são divididos de acordo com o número de dias morados
		4. A quantia excedente é quanto cada morador gastou além da franquia a que tinha direito
		5. A quantia excedente que cada morador deve pagar pode ser compensado pelo faltante de outro morador em atingir sua franquia
		
		Saída: (resumo, rateio)
		-----------------------
		
		resumo:
			Dicionário com as chaves:
			* total_telefonemas
			* total_conta
			* total_dias
			* total_sem_dono
			* total_ex_moradores
		
		rateio[morador]:
			Classe MoradorRateio com os campos:
			* qtd_dias
			* gastos
			* franquia
			* sem_dono
			* excedente
			* servicos
			* a_pagar
		
		'''
		periodo = self.republica.periodo_fechamento(self.emissao)
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
			quantia = telefonema.quantia if type(telefonema.quantia) is Decimal else str(telefonema.quantia)
			
			total_telefonemas += quantia
			morador = telefonema.responsavel
			if morador:
				if morador not in rateio:
					# ex-morador que tem telefonema pendente
					rateio[morador]          = MoradorRateio()
					rateio[morador].qtd_dias = Decimal(0)
					rateio[morador].gastos   = Decimal(0)
					total_ex_moradores += telefonema.quantia
				
				rateio[morador].gastos += quantia
			else:
				total_sem_dono += telefonema.quantia
		
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
	has_field('quantia',        Money(10, 2),   nullable = False)
	many_to_one('responsavel',    of_kind = 'Morador',       colname = 'id_morador')
	many_to_one('conta_telefone', of_kind = 'ContaTelefone', colname = 'id_conta_telefone', inverse = 'telefonemas', column_kwargs = dict(primary_key = True))
	using_options(tablename = 'telefonema')


class Morador(Entity):
	has_field('data_entrada', Date, default = date.today, nullable = False)
	has_field('data_saida', Date)
	many_to_one('republica', of_kind = 'Republica', colname = 'id_republica', column_kwargs = dict(nullable = False))
	many_to_one('pessoa', of_kind = 'Pessoa', colname = 'id_pessoa', column_kwargs = dict(nullable = False))
	one_to_many('despesas_periodicas', of_kind = 'DespesaPeriodica', inverse = 'responsavel', order_by = 'proximo_vencimento')
	one_to_many('telefones_sob_responsabilidade', of_kind = 'TelefoneRegistrado', inverse = 'responsavel')
	using_options(tablename = 'morador')
	# UniqueConstraint ainda não funciona nessa versão do elixir. Veja http://groups.google.com/group/sqlelixir/browse_thread/thread/46a2733c894e510b/048cde52cd6afa35?lnk=gst&q=UniqueConstraint&rnum=3#048cde52cd6afa35
	#using_table_options(UniqueConstraint('id_pessoa', 'id_republica', 'data_entrada'))
	
	
	def _get_despesas(self, data_inicial, data_final):
		return Despesa.select(
					and_(
						Despesa.c.id_morador == self.id,
						Despesa.c.data       >= data_inicial,
						Despesa.c.data       <= data_final
						),
					order_by = Despesa.c.data
					)
	
	
	def _cadastrar_despesas_periodicas(self, data_inicial, data_final):
		for despesa in self.despesas_periodicas:
			data_ref = data_final if not despesa.data_termino else min(despesa.data_termino, data_final)
			while despesa.proximo_vencimento <= data_ref:
				nova_despesa = Despesa(
						data        = despesa.proximo_vencimento,
						quantia     = despesa.quantia,
						responsavel = despesa.responsavel,
						tipo        = despesa.tipo
					)
				nova_despesa.flush()
				despesa.proximo_vencimento += relativedelta(months = 1)
				
			if despesa.data_termino and \
				((despesa.data_termino < data_final) or
				 (despesa.data_termino < despesa.proximo_vencimento)):
				despesa.delete()
			
			despesa.flush()
	
	
	def despesas(self, data_inicial, data_final):
		self._cadastrar_despesas_periodicas(data_inicial, data_final)
		return self._get_despesas(data_inicial, data_final)
	
	
	def total_despesas(self, data_inicial, data_final):
		'''
		Atualmente esta função está servindo apenas como referência da utilização de algumas funções do SQLAlchemy.
		O mesmo resultado pode ser obtido através de uma "List comprehension"
		'''
		def total(especifica):
			return select(
				[func.coalesce(func.sum(Despesa.c.quantia), 0)],
				and_(
					Despesa.c.id_morador == self.id,
					Despesa.c.data >= data_inicial,
					Despesa.c.data <= data_final,
					Despesa.c.id_tipo == TipoDespesa.c.id,
					TipoDespesa.c.especifica == especifica,
					)
				).execute().fetchone()[0]
				
		return (total(especifica = False), total(especifica = True))
	
	
	
	def despesas_por_tipo(self, tipo_despesa, data_inicial = None, data_final = None):
		return [despesa for despesa in self.despesas(data_inicial, data_final) if despesa.tipo == tipo_despesa]
	
	
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
		entrada  = max(self.data_entrada, data_inicial)
		saida    = min(self.data_saida, data_final) if self.data_saida else data_final
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
	has_field('quantia', Money(10, 2), nullable = False)
	using_options(tablename = 'despesa')
	many_to_one('responsavel',  of_kind = 'Morador',     colname = 'id_morador',      column_kwargs = dict(nullable = False))
	many_to_one('tipo',         of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))



class DespesaPeriodica(Entity):
	has_field('proximo_vencimento', Date, default = date.today, nullable = False)
	has_field('quantia', Money(10,2), nullable = False)
	has_field('data_termino', Date)
	using_options(tablename = 'despesa_periodica')
	many_to_one('responsavel',  of_kind = 'Morador', colname = 'id_morador', inverse = 'despesas_periodicas', column_kwargs = dict(nullable = False))
	many_to_one('tipo', of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))


#
# identity model
# 

class Visit(Entity):
    has_field('visit_key', String(40), primary_key=True)
    has_field('created', DateTime, nullable=False, default=datetime.now)
    has_field('expiry', DateTime)
    using_options(tablename='visit')
    
    @classmethod
    def lookup_visit(cls, visit_key):
        return Visit.get(visit_key)

class VisitIdentity(Entity):
    has_field('visit_key', String(40), primary_key=True)
    many_to_one('user', of_kind='User', colname='user_id', use_alter=True)
    using_options(tablename='visit_identity')

class Group(Entity):
    has_field('group_id', Integer, primary_key=True)
    has_field('group_name', Unicode(16), unique=True)
    has_field('display_name', Unicode(255))
    has_field('created', DateTime, default=datetime.now)
    many_to_many('users', of_kind='User', inverse='groups')
    many_to_many('permissions', of_kind='Permission', inverse='groups')
    using_options(tablename='tg_group')

class User(Entity):
    has_field('user_id', Integer, primary_key=True)
    has_field('user_name', Unicode(16), unique=True)
    has_field('email_address', Unicode(255), unique=True)
    has_field('display_name', Unicode(255))
    has_field('password', Unicode(40))
    has_field('created', DateTime, default=datetime.now)
    many_to_many('groups', of_kind='Group', inverse='users')
    using_options(tablename='tg_user')
    
    @property
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

class Permission(Entity):
    has_field('permission_id', Integer, primary_key=True)
    has_field('permission_name', Unicode(16), unique=True)
    has_field('description', Unicode(255))
    many_to_many('groups', of_kind='Group', inverse='permissions')
    using_options(tablename='permission')
