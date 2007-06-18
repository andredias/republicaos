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
	
	def __repr__(self):
		return "<nome:'%s'>" % self.nome.encode('utf-8')









class Contato(Entity):
	has_field('contato', Unicode(100), nullable = False),
	has_field('tipo', Integer, nullable = False),
	many_to_one('pessoa', of_kind = 'Pessoa', inverse = 'contatos', colname = 'id_pessoa',
		column_kwargs = dict(nullable = False))
	using_options(tablename = 'contato')
	
	def __repr__(self):
		return '<contato:%s, pessoa:%s>' % (self.contato.encode('utf-8'), self.pessoa.nome.encode('utf-8'))










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
		return "<número: %d, república: '%s', responsável: '%s'>" % (self.numero, self.republica.nome.encode('utf-8'), self.responsavel.pessoa.nome.encode('utf-8'))







class Republica(Entity):
	has_field('nome', Unicode(80), nullable = False)
	has_field('data_criacao', Date, default = date.today, nullable = False)
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
	
	
	def __repr__(self):
		return '<nome:%s, data_criação:%s>' % \
				(self.nome.encode('utf-8'), self.data_criacao.strftime('%d/%m/%Y'))
	
	
	def after_insert(self):
		criar_fechamento(self.data_criacao + relativedelta(months = 1))
	
	
	def fechamento_na_data(self, data = None):
		'''
		Fechamento em que determinada data está contida
		'''
		if not data:
			data = date.today()
		
		if len(self.fechamentos) and (self.fechamentos[0].data > data >= self.data_criacao):
			for i in range(len(self.fechamentos) - 1):
				if self.fechamentos[i].data > data >= self.fechamentos[i + 1].data:
					return self.fechamentos[i]
			return self.fechamentos[-1]
		else:
			return None
	
	
	def criar_fechamento(self, data = None):
		if not data:
			data = (self.fechamentos[0].data if len(self.fechamentos) else self.data_criacao) + relativedelta(months = 1)
		novo_fechamento = Fechamento(data = data, republica = self)
		novo_fechamento.flush()
		# Elixir não está garantindo o Backref automaticamente
		if novo_fechamento not in self.fechamentos:
			self.fechamentos.append(novo_fechamento)
			self.fechamentos.sort(key = lambda obj: obj.data, reverse = True)
		return novo_fechamento
	
	
	def moradores(self, data_inicial = None, data_final = None):
		'''
		Retorna os moradores da república no período de tempo
		'''
		moradores =  Morador.select(
						and_(
							Morador.c.id_republica == self.id,
							Morador.c.data_entrada < data_final,
							or_(Morador.c.data_saida >= data_inicial, Morador.c.data_saida == None)
						)
					)
		moradores.sort(key = lambda obj: obj.pessoa.nome)
		return moradores
	
	
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
			if registro not in self.telefones_registrados:
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
	def __repr__(self):
		if hasattr(self, 'franquia'): # usado no rateio da conta de telefone
			return '<qtd_dias:%d, franquia:%s, gastos:%s, sem dono:%s, excedentes:%s, serviços:%s, a pagar:%s>' % \
				(self.qtd_dias, self.franquia, self.gastos, self.sem_dono, self.excedente, self.servicos, self.a_pagar)
		else:
			return '<qtd_dias:%d, quota:%s, quota_telefone:%s, total_despesas:%s, saldo_final:%s>' % \
				(self.qtd_dias, self.quota, self.quota_telefone, self.total_despesas, self.saldo_final)







class Fechamento(Entity):
	has_field('data', Date, primary_key = True)
	using_options(tablename = 'fechamento')
	many_to_one('republica', of_kind = 'Republica', inverse = 'fechamentos', colname = 'id_republica',
		column_kwargs = dict(primary_key = True))
	
	def __repr__(self):
		return "<fechamento:%s [%s, %s], república:'%s'>" % \
			(
			self.data.strftime('%d/%m/%Y'),
			self.data_inicial.strftime('%d/%m/%Y'),
			self.data_final.strftime('%d/%m/%Y'),
			self.republica.nome.encode('utf-8')
			)
	
	
	def setup(self):
		'''
		Idealmente, esta rotina deveria ser executada depois que o fechamento é carregado do BD
		'''
		self._data_final = self.data - relativedelta(days = 1)
		if self.data > self.republica.fechamentos[-1].data :
			self._data_inicial = self.republica.fechamentos[self.republica.fechamentos.index(self) + 1].data
		else:
			self._data_inicial = self.republica.data_criacao
	
	
	@property
	def data_inicial(self):
		if not hasattr(self, '_data_inicial'):
			self.setup()
		return self._data_inicial
	
	@property
	def data_final(self):
		if not hasattr(self, '_data_final'):
			self.setup()
		return self._data_final
	
	
	def executar_rateio(self):
		'''
		Calcula a divisão das despesas em determinado período
		'''
		data_inicial, data_final = self.data_inicial, self.data_final
		
		moradores = set(self.republica.moradores(data_inicial, data_final))
		despesas  = list()
		rateio    = dict()
		
		# Divisão das contas de telefone
		contas_telefone = self.republica.contas_telefone(data_inicial, data_final)
		for conta_telefone in contas_telefone:
			conta_telefone.executar_rateio()
			moradores.update(set(conta_telefone.rateio.keys()))
		
		# Contabilização das despesas pagas por cada morador
		for morador in moradores:
			rateio[morador]                = MoradorRateio()
			rateio[morador].qtd_dias       = morador.qtd_dias_morados(data_inicial, data_final)
			rateio[morador].total_despesas = Decimal(0)
			
			despesas_morador = morador.despesas(data_inicial, data_final)
			despesas.extend(despesas_morador)
			rateio[morador].total_despesas = sum(despesa.quantia for despesa in despesas_morador)
			rateio[morador].quota_telefone = sum(conta_telefone.rateio[morador].a_pagar for conta_telefone in contas_telefone if morador in conta_telefone.rateio)
			
		# Divisão das contas
		total_despesas = sum(despesa.quantia for despesa in despesas)
		total_dias     = sum(rateio[morador].qtd_dias for morador in moradores)
		total_telefone = sum(rateio[morador].quota_telefone for morador in moradores)
		for morador in moradores:
			# o total do telefone é uma despesa específica e não deve ser usada no cálculo das quotas
			# a parte de cada um nos telefones é contabilizada no saldo final
			rateio[morador].quota       = (total_despesas - total_telefone) * rateio[morador].qtd_dias / total_dias
			rateio[morador].porcentagem = 100 * rateio[morador].qtd_dias / total_dias
			rateio[morador].saldo_final = rateio[morador].quota + rateio[morador].quota_telefone - rateio[morador].total_despesas
		
		self.total_despesas  = total_despesas
		self.total_dias      = total_dias
		self.total_telefone  = total_telefone
		self.despesas        = despesas
		self.contas_telefone = contas_telefone
		self.rateio          = rateio
		self.participantes   = list(moradores)
		self.total_tipo_despesa = dict(
			[(tipo_despesa, sum(despesa.quantia for despesa in despesas if despesa.tipo == tipo_despesa))
			for tipo_despesa in self.republica.tipos_despesa]
		)
		
		for tipo, total in self.total_tipo_despesa.items():
			if not total: # total == 0
				self.total_tipo_despesa.pop(tipo)
		
		self.despesas.sort(key = lambda obj:(obj.data, obj.responsavel.pessoa.nome))
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
		credores.sort(key =  lambda obj: (self.rateio[obj].saldo_final, obj.pessoa.nome))
		devedores.sort(key = lambda obj: (self.rateio[obj].saldo_final, obj.pessoa.nome), reverse = True)
		
		self.acerto_a_pagar   = dict([(devedor, dict()) for devedor in devedores])
		self.acerto_a_receber = dict([(credor, dict()) for credor in credores])
		if len(devedores) == 0: return
		
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
			for devedor in self.acerto_a_pagar.keys():
				for credor in self.acerto_a_pagar[devedor].keys():
					self.acerto_a_receber[credor][devedor] = self.acerto_a_pagar[devedor][credor]
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
	
	
	def __repr__(self):
		return '<telefone: %d, emissão: %s, república: %s>' % \
				(self.telefone, self.emissao.strftime('%d/%m/%Y'), self.republica.nome.encode('utf-8'))
	
	
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
		tipos_fone      = {'FIXO':0, 'CELULAR':1, 'MOVEL':1, 'NETFONE':2}
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
				for tipo in tipos_fone.keys():
					if tipo in descricao:
						tipo_fone = tipos_fone[tipo]
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
			* porcentagem
			* gastos
			* franquia
			* sem_dono
			* excedente
			* servicos
			* a_pagar
		
		'''
		fechamento = self.republica.fechamento_na_data(self.emissao)
		rateio = dict()
		
		total_dias = 0
		# determina os moradores atuais da república
		for morador in self.republica.moradores(fechamento.data_inicial, fechamento.data_final):
			qtd_dias    = morador.qtd_dias_morados(fechamento.data_inicial, fechamento.data_final)
			total_dias += qtd_dias
			rateio[morador]          = MoradorRateio()
			rateio[morador].qtd_dias = Decimal(qtd_dias) # Decimal pois vai ser usado em outras contas depois
			rateio[morador].gastos   = Decimal(0)
		
		# Cálculo dos telefonemas de acordo com o responsável: morador, ex-morador ou sem dono
		total_sem_dono     = Decimal(0)
		total_ex_moradores = Decimal(0)
		total_telefonemas  = Decimal(0)
		for telefonema in self.telefonemas:
			quantia = telefonema.quantia if type(telefonema.quantia) is Decimal else Decimal(str(telefonema.quantia))
			
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
			
			morador.porcentagem = morador.qtd_dias * 100 / total_dias
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
	
	def __repr__(self):
		return "<número:%d, quantia:%s, segundos:%s, responsável:'%s'>" % \
			(self.numero, self.quantia, self.segundos, (self.responsavel.pessoa.nome.encode('utf-8') if self.responsavel else ''))


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
	
	def __repr__(self):
		return "<pessoa:'%s', república:'%s', data_entrada:%s>" % \
			(self.pessoa.nome.encode('utf-8'), self.republica.nome.encode('utf-8'), self.data_entrada.strftime('%d/%m/%Y'))
	
	
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
	has_field('descricao', String)
	using_options(tablename = 'tipo_despesa')
	many_to_one('republica', of_kind = 'Republica', inverse = 'tipo_despesas', column_kwargs = dict(nullable = False))
	
	def __repr__(self):
		return '<nome:%s>' % self.nome.encode('utf-8')


class Despesa(Entity):
	has_field('data', Date, default = date.today, nullable = False)
	has_field('quantia', Money(10, 2), nullable = False)
	using_options(tablename = 'despesa')
	many_to_one('responsavel',  of_kind = 'Morador',     colname = 'id_morador',      column_kwargs = dict(nullable = False))
	many_to_one('tipo',         of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))
	
	def __repr__(self):
		return '<data:%s, quantia:%s, tipo:%s, responsável:%s>' % \
			(self.data.strftime('%d/%m/%Y'), self.quantia, self.tipo.nome.encode('utf-8'), self.responsavel.pessoa.nome.encode('utf-8'))


class DespesaPeriodica(Entity):
	has_field('proximo_vencimento', Date, default = date.today, nullable = False)
	has_field('quantia', Money(10,2), nullable = False)
	has_field('data_termino', Date)
	using_options(tablename = 'despesa_periodica')
	many_to_one('responsavel',  of_kind = 'Morador', colname = 'id_morador', inverse = 'despesas_periodicas', column_kwargs = dict(nullable = False))
	many_to_one('tipo', of_kind = 'TipoDespesa', colname = 'id_tipo_despesa', column_kwargs = dict(nullable = False))
	
	def __repr__(self):
		return "<próximo_vencimento:%s, data_termino:%s, quantia:%s, tipo:'%s', responsável:'%s'>" % \
			(self.proximo_vencimento.strftime('%d/%m/%Y'), (self.data_termino.strftime('%d/%m/%Y') if self.data_termino else ''), self.quantia, self.tipo.nome.encode('utf-8'), self.responsavel.pessoa.nome.encode('utf-8'))


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
