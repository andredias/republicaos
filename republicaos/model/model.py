# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from elixir      import Unicode, Boolean, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, using_options, using_table_options, using_mapper_options
from elixir      import Field, OneToMany, ManyToOne
from sqlalchemy  import types, and_, or_, select, UniqueConstraint, func
from sqlalchemy.orm import reconstructor
from sqlalchemy.sql.expression import desc
from datetime    import date, datetime, time
import csv
import elixir
from decimal     import Decimal
from dateutil.relativedelta import relativedelta
from republicaos.model import Session
from hashlib import sha1



import logging

log = logging.getLogger(__name__)





class ModelIntegrityException(Exception):
    pass

def check_se_morou_periodo(entrada_morador, saida_morador, inicio_periodo, fim_periodo):
    '''
    Verifica se o período morado está dentro do intervalo especificado.
    '''
    return entrada_morador < fim_periodo and (saida_morador == None or inicio_periodo <= saida_morador)


class Pessoa(Entity):
    nome = Field(Unicode(30), required=True)
    _senha = Field(String(40), required=True)
    email = Field(String(80), required=True, unique=True)
    data_cadastro = Field(Date, required=True, default=date.today)

    @classmethod
    def encrypt_senha(cls, password):
        return sha1(password).hexdigest()


    def _set_senha(self, password):
        self._senha = self.encrypt_senha(password)

    def _get_senha(self):
        return self._senha

    senha = property(_get_senha, _set_senha)

    def __repr__(self):
        return "Pessoa <nome:'%s', data_cadastro: %r>" % (self.nome, self.data_cadastro)



    #def telefonemas(self, conta_telefone):
        #if conta_telefone.republica is not self.republica:
            #return None
        #return Telefonema.query.filter(
                    #and_(
                        #Telefonema.conta_telefone == conta_telefone,
                        #Telefonema.responsavel == self
                        #)
                    #).order_by(Telefonema.numero).all()



    def get_qtd_dias_morados(self, republica, data_inicial = None, data_final = None):
        if not data_inicial:
            data_inicial = republica.data_criacao
        if not data_final:
            data_final = date.today()
        intervalos = select(
                    [
                        func.max(Morador.entrada, data_inicial),
                        func.min(func.coalesce(Morador.saida, data_final), data_final)
                    ],
                    whereclause = and_(
                        Morador.republica == republica,
                        Morador.pessoa == self,
                        Morador.entrada <= data_final,
                        or_(Morador.saida == None, Morador.saida >= data_inicial)
                    )
                ).execute().fetchall()

        log.debug('Pessoa<%s>.qtd_dias_morados(%r, %r, %r): %r' % (self.nome, republica, data_inicial, data_final, intervalos))
        qtd_dias = 0
        for entrada, saida in intervalos:
            qtd_dias += (saida - entrada).days + 1

        return qtd_dias
    
    @property
    def morador_em_republicas(self):
        hoje = date.today()
        return Republica.query.filter(
                                and_(
                                    Morador.republica_id == Republica.id,
                                    Morador.pessoa == self,
                                    Morador.entrada <= hoje,
                                    Morador.saida == None
                                    )
                                ).order_by(desc(Morador.entrada)).all()
    
    @property
    def ex_morador_em_republicas(self):
        hoje = date.today()
        return Republica.query.filter(
                                and_(
                                    Morador.republica_id == Republica.id,
                                    Morador.pessoa == self,
                                    Morador.saida < hoje
                                    )
                                ).order_by(desc(Morador.saida)).all()








class Morador(Entity):
    entrada = Field(Date, required=True, primary_key = True)
    saida = Field(Date)
    peso_aluguel = Field(Numeric(5,2))
    pessoa = ManyToOne('Pessoa', required=True, primary_key = True)
    republica = ManyToOne('Republica', required=True, primary_key = True)

    def __repr__(self):
        return 'Morador <pessoa_id: %s, republica_id: %s, entrada: %r, saida: %r>' % (self.pessoa.id, self.republica.id, self.entrada,
                self.saida)


    @classmethod
    def get_moradores(self, republica, data_inicial = None, data_final = None):
        '''
        Retorna os moradores da república no período de tempo
        '''
        data_inicial = data_inicial or data_final
        if not data_inicial:
            clausula_data = None
        else:
            if not data_final:
                data_final = data_inicial
            else:
                data_final = max(data_inicial, data_final)
            clausula_data = and_(Morador.entrada < data_final,
                        or_(Morador.saida >= data_inicial, Morador.saida == None))
    
        moradores =  Pessoa.query.filter(
                        and_(
                            Morador.republica == republica,
                            clausula_data,
                            Morador.pessoa_id == Pessoa.id
                        )
                    ).distinct().order_by(Pessoa.nome).all()
        log.debug('Morador.get_moradores(%r, %r, %r): %r' % (republica, data_inicial, data_final, moradores))
        return moradores


    @classmethod
    def get_republicas(cls, pessoa, data_inicial = None, data_final = None):
        '''
        Retorna as repúblicas em que uma pessoa morou num período
        '''
        data_inicial = data_inicial or data_final
        if not data_inicial:
            clausula_data = None
        else:
            if not data_final:
                data_final = data_inicial
            else:
                data_final = max(data_inicial, data_final)
            clausula_data = and_(Morador.entrada < data_final,
                        or_(Morador.saida == None, Morador.saida >= data_inicial))

        republicas =  Republica.query.filter(
                        and_(
                            Morador.pessoa == pessoa,
                            clausula_data,
                            Morador.republica_id == Republica.id
                        )
                    ).distinct().order_by(Republica.nome).all()
        log.debug('Morador.get_republicas(%s, %r, %r): %r' % (pessoa, data_inicial, data_final, moradores))
        return republicas


    @classmethod
    def get_intervalos_de_moradores(cls, republica, data_inicial, data_final):
        '''
        Retorna os intervalos que houve moradores diferentes durante um determinado período de apuração
        '''
        # define os intervalos
        moradores = Morador.query.filter(
                        and_(
                            Morador.entrada < data_final,
                            or_(Morador.saida == None, Morador.saida >= data_inicial),
                            Morador.republica == republica
                        )
                    ).distinct().all()
        datas = set([self.data_inicial, self.data_final])
        for morador in moradores:
            datas.add(morador.entrada)
            if saida:
                datas.add(morador.saida)
        datas = sorted(datas)
        intervalos = (Intervalo(datas[i], datas[i+1]) for i in range(len(datas) - 1))

        # define quem está em que intervalo
        for intervalo in intervalos:
            intervalo.participantes = [morador for morador in moradores if check_se_morou_no_periodo(morador.entrada,
                                            morador.saida, intervalo.data_inicial, intervalo.data_final)]

        log.debug('Morador.get_intervalos_de_moradores(%r, %r, %r): %r' % (republica, data_inicial, data_final, intevalos))
        return intervalos








class TelefoneRegistrado(Entity):
    '''
    TelefoneRegistrado registrado na república tendo algum morador como responsável.

    Não poderá haver mais de um morador sendo responsável pelo telefone em uma república. Essa restrição
    é reforçada pela chave primária.
    '''
    numero      = Field(Numeric(12, 0), primary_key = True)
    descricao   = Field(Unicode)
    republica   = ManyToOne('Republica', primary_key = True)
    responsavel = ManyToOne('Pessoa', required = True)
    using_options(tablename = 'telefone')






class Republica(Entity):
    nome         = Field(Unicode(90), required = True)
    data_criacao = Field(Date, default = date.today, required = True)
    logradouro   = Field(Unicode(150), required = True)
    complemento  = Field(Unicode(100))
    cidade       = Field(Unicode(80), required = True)
    uf           = Field(String(2), required = True)

    fechamentos           = OneToMany('Fechamento', order_by = '-data')
    tipos_despesa         = OneToMany('TipoDespesa', order_by = 'nome')
    telefones_registrados = OneToMany('TelefoneRegistrado', order_by = 'numero')


    def __repr__(self):
        return 'Republica: <nome: %s, data_criacao: %r>' % (self.nome.encode('utf-8'), self.data_criacao)


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
        return Fechamento(data = data, republica = self)


    def get_moradores(self, fechamento = None, data_inicial = None, data_final = None):
        '''
        Retorna os moradores da república no período de tempo
        '''
        if fechamento:
            data_inicial = fechamento.data_inicial
            data_final = fechamento.data_inicial
        return Morador.get_moradores(self, data_inicial, data_final)

        # o trecho abaixo não funcionou como o esperado porque Morador.pessoa está voltando todo o registro de morador novamente
        # mesmo se voltasse só pessoa_id, seria necessário várias consultas para reconstruir objetos de pessoas.
        #consulta = select(
                    #[Morador.pessoa, Morador.entrada, func.coalesce(Morador.saida, data_final)],
                    #whereclause = and_(
                        #Morador.republica == republica,
                        #Morador.entrada <= data_final,
                        #or_(Morador.saida == None, Morador.saida >= data_inicial)
                    #)
                #).order_by(Morador.pessoa).execute().fetchall()



        #pessoa_ref = None
        #result = {}
        #for pessoa, entrada, saida in consulta:
            #if pessoa != pessoa_ref:
                #result[pessoa] = 0
                #pessoa_ref = pessoa
            #result[pessoa_ref] += (saida - entrada).days

        #return result


    def contas_telefone(self, data_inicial, data_final):
        '''
        Retorna as contas de telefone da república no período
        '''
        return ContaTelefone.query.filter(
                    and_(
                        ContaTelefone.republica == self,
                        ContaTelefone.emissao >= data_inicial,
                        ContaTelefone.emissao <= data_final
                    )
                ).all()



    def registrar_responsavel_telefone(self, numero, responsavel = None, descricao = None):
        telefone = None
        for telefone_ja_registrado in self.telefones_registrados:
            if numero == telefone_ja_registrado.numero:
                telefone = telefone_ja_registrado
                break

        if responsavel:
            assert responsavel.republica == self

        if telefone and responsavel:
            telefone.responsavel = responsavel
            telefone.descricao   = descricao
        elif not telefone and responsavel:
            novo_tel = TelefoneRegistrado(numero = numero, republica = self, responsavel = responsavel, descricao = descricao)
        elif telefone and not responsavel: # não há mais responsável
            telefone.delete()

        return






class Fechamento(Entity):
    data      = Field(Date, primary_key = True)
    republica = ManyToOne('Republica', primary_key = True)

    @reconstructor
    def setup(self):
        self.rateado = False # mostra se o rateio já foi feito
        self.data_final = self.data - relativedelta(days = 1)
        if self.data > self.republica.fechamentos[-1].data :
            self.data_inicial = self.republica.fechamentos[self.republica.fechamentos.index(self) + 1].data
        else:
            self.data_inicial = self.republica.data_criacao


    def executar_rateio(self):
        '''
        Calcula a divisão das despesas em determinado período
        '''
        self.setup()
        self.rateado = True

        # todos os participantes deste fechamento
        self.participantes = set()

        # Divisão das contas de telefone
        #contas_telefone = self.republica.contas_telefone(data_inicial, data_final)
        #for conta_telefone in contas_telefone:
            #conta_telefone.executar_rateio()
            #self.participantes.update(set(conta_telefone.rateio.keys()))

        # incluir todos os cadastrados como morador
        self.participantes.update(set(self.republica.get_moradores(self)))
        self.participantes = sorted(self.participantes, key = lambda obj:obj.nome)

        # preencher rateio de telefone
        #self.quota_telefone = dict(
                        #(pessoa, sum(conta_telefone.rateio[morador].a_pagar for conta_telefone in contas_telefone if pessoa in conta_telefone.rateio))
                        #for pessoa in self.participantes
                    #)
        #self.total_telefone = sum(quota_telefone for quota_telefone in self.quota_telefone.values)

        # obtem despesas
        despesas = Despesa.get_despesas_no_periodo(republica=self.republica, data_inicial=self.data_inicial, data_final=self.data_final)
        self.despesas = dict(
                                (pessoa, sum(despesa.quantia for despesa in despesas if despesa.responsavel == pessoa))
                                for pessoa in self.participantes
                            )
        self.total_despesas = sum(despesa.quantia for despesa in despesas)


        tipos_despesa = set(despesa.tipo for despesa in despesas)
        self.total_tipo_despesa = dict(
                                        (tipo_despesa.nome, sum(despesa.quantia for despesa in despesas if despesa.tipo == tipo_despesa))
                                        for tipo_despesa in tipos_despesa
                                    )


        # Definição de quantidades de dias morados para executar média ponderada
        self.qtd_dias_morados = dict(
                                        (pessoa, pessoa.get_qtd_dias_morados(self.republica, self.data_inicial, self.data_final))
                                        for pessoa in self.participantes
                                    )
        self.total_dias_morados = sum(dias for dias in self.qtd_dias_morados.values())

        #
        # Divisão das quotas
        #
        self.quota = dict()
        self.porcentagem = dict()
        self.saldo_final = dict()
        for pessoa in self.participantes:
            # o total do telefone é uma despesa específica e não deve ser usada no cálculo das quotas
            # a parte de cada um nos telefones é contabilizada no saldo final
            #self.quota[pessoa] = (self.total_despesas - self.total_telefone) * self.qtd_dias_morados[pessoa] / self.total_dias_morados
            self.quota[pessoa] = self.total_despesas * self.qtd_dias_morados[pessoa] / self.total_dias_morados
            self.porcentagem[pessoa] = 100 * self.qtd_dias_morados[pessoa] / self.total_dias_morados
            #self.saldo_final[pessoa] = self.quota[pessoa] + self.quota_telefone[pessoa] - self.despesas[pessoa]
            self.saldo_final[pessoa] = self.quota[pessoa] - self.despesas[pessoa]

        #
        # Acerto de contas
        #
        credores  = [pessoa for pessoa in self.participantes if self.saldo_final[pessoa] <= 0]
        devedores = list(set(self.participantes) - set(credores))

        # ordena a lista de credores e devedores de acordo com o saldo_final
        credores.sort(key =  lambda obj: (self.saldo_final[obj], obj.nome))
        devedores.sort(key = lambda obj: (self.saldo_final[obj], obj.nome), reverse = True)

        self.acerto_a_pagar   = dict((devedor, {}) for devedor in devedores)
        self.acerto_a_receber = dict((credor, {}) for credor in credores)
        if len(devedores) == 0: return

        devedores = iter(devedores)
        try:
            devedor     = devedores.next()
            saldo_pagar = self.saldo_final[devedor]
            for credor in credores:
                saldo_receber = abs(self.saldo_final[credor])
                while (saldo_receber > 0):
                        if saldo_receber >= saldo_pagar:
                            self.acerto_a_pagar[devedor][credor] = saldo_pagar
                            saldo_receber -= saldo_pagar
                            devedor        = devedores.next()
                            saldo_pagar    = self.saldo_final[devedor]
                        else:
                            self.acerto_a_pagar[devedor][credor] = saldo_receber
                            saldo_pagar  -= saldo_receber
                            saldo_receber = 0
        except StopIteration:
            pass

        for devedor in self.acerto_a_pagar:
            for credor in self.acerto_a_pagar[devedor]:
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



class RateioContaTelefone(object):
    def __init__(self, conta_telefone):
        '''
        Divide a conta de telefone.

        Critérios:
        1. Os telefonemas sem dono são debitados da franquia
        2. A franquia restante é dividida entre os participantes de acordo com o a quota de cada um
        3. Os serviços (se houverem) também são divididos de acordo com o número de dias morados
        4. A quantia excedente é quanto cada participante gastou além da franquia a que tinha direito
        5. A quantia excedente que cada participante deve pagar pode ser compensado pelo faltante de outro participante em atingir sua franquia
        '''
        self.conta_telefone = conta_telefone

        # Determina os excedentes e calcula os abonos de moradores e ex-moradores
        # Esses valores são armazenados pois o cálculo constante é mais dispendioso em termos de processamento
        self._excedente = dict([(participante, self.devido(participante) - self.franquia(participante)) for participante in conta_telefone.participantes])
        self._abono     = dict([(participante, Decimal(0)) for participante in conta_telefone.participantes])
        sobra_franquia  = sum(abs(self._excedente[morador]) for morador in self.conta_telefone.moradores if self._excedente[morador] < 0)

        # divisão da sobra de franquia entre os moradores que excederam sua quota
        # a sobra de franquia de uns vai ser usada para compensar o excedente de outros
        excedentes = [morador for morador in self.conta_telefone.moradores if self._excedente[morador] > 0]
        while (not float_equal(sobra_franquia, 0)) and excedentes:
            total_quota = sum(conta_telefone.fechamento.quota(morador) for morador in excedentes)
            total_abono = Decimal(0)
            for morador in excedentes:
                excedente = self.excedente(morador)
                abono     = sobra_franquia * conta_telefone.fechamento.quota(morador) / total_quota
                abono     = abono if abono <= excedente else excedente
                self._abono[morador] += abono
                total_abono          += abono
            sobra_franquia -= total_abono
            excedentes      = [morador for morador in excedentes if not float_equal(self._abono[morador], self._excedente[morador])]

        # se ainda há sobra de franquia, então distribuir entre os ex-moradores
        excedentes = list(conta_telefone.ex_moradores)
        while (not float_equal(sobra_franquia, 0)) and excedentes:
            quota_sobra = sobra_franquia / len(excedentes)
            total_abono = Decimal(0)
            for ex_morador in excedentes:
                excedente = self.devido(ex_morador)
                abono     = quota_sobra if quota_sobra <= excedente else excedente # todo a_pagar de ex-morador já é o excesso
                self._abono[ex_morador] += abono
                total_abono             += abono
            sobra_franquia -= total_abono
            excedentes      = [ex_morador for ex_morador in excedentes if not float_equal(self._abono[ex_morador], self._excedente[ex_morador])]



    def telefonemas(self, participante):
        '''
        Telefonemas do participante
        '''
        if participante not in self.conta_telefone.participantes:
            return 0
        return sum(telefonema.quantia for telefonema in self.conta_telefone.telefonemas if telefonema.responsavel is participante)


    def extras(self, participante):
        '''
        Relativo aos rateio dos telefonemas sem dono e dos serviços
        '''
        return self.conta_telefone.fechamento.quota(participante) * \
                (self.conta_telefone.total_sem_dono + self.conta_telefone.servicos) / Decimal(100)


    def franquia(self, participante):
        return self.conta_telefone.fechamento.quota(participante) * \
                (self.conta_telefone.franquia + self.conta_telefone.servicos) / Decimal(100)


    def devido(self, participante):
        return self.telefonemas(participante) + self.extras(participante)


    def excedente(self, participante):
        return self._excedente[participante] if participante in self._excedente else Decimal(0)


    def abono(self, participante):
        return self._abono[participante] if participante in self._abono else Decimal(0)


    def a_pagar(self, participante):
        if self.excedente(participante) > 0:
            return self.devido(participante) - self.abono(participante)
        else:
            return self.franquia(participante)



class ContaTelefone(Entity):
    '''
    Representa cada conta de telefone que chega por mês para a república.
    '''
    # campo id implícito
    vencimento = Field(Date, required = True)
    emissao = Field(Date, required = True)
    telefone = Field(Numeric(12, 0), required = True)
    operadora_id = Field(Integer, required = True)
    franquia = Field(Numeric(10,2), default = 0)
    servicos = Field(Numeric(10,2), default = 0)
    republica = ManyToOne('Republica', required = True)
    telefonemas = OneToMany('Telefonema', order_by = 'numero')

    using_options(tablename = 'conta_telefone')
    using_table_options(UniqueConstraint('telefone', 'emissao'))


    @property
    def rateio(self):
        if not hasattr(self, '_rateio'):
            self._rateio = RateioContaTelefone(self)
        return self._rateio

    def determinar_responsaveis_telefonemas(self):
        '''
        Determina os responsáveis pelos telefonemas da conta
        '''
        numeros_registrados = dict([(tr.numero, tr) for tr in self.republica.telefones_registrados])
        for telefonema in self.telefonemas:
            if telefonema.responsavel is None and telefonema.numero in numeros_registrados:
                telefonema.responsavel = numeros_registrados[telefonema.numero].responsavel

        return


    def telefonema(self, numero):
        for telefonema in self.telefonemas:
            if numero == telefonema.numero:
                return telefonema
        return None


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

        if self.operadora_id == 1:
            func_interpreta_csv = self._interpreta_csv_net_fone
        else:
            func_interpreta_csv = None

        #arquivo precisa ser uma lista de linhas
        if isinstance(arquivo, basestring):
            arquivo = arquivo.encode('utf-8')
            arquivo = arquivo.strip().splitlines()

        linhas = [linha for linha in csv.reader(arquivo)]
        telefonemas, encargos = func_interpreta_csv(linhas)

        if encargos > 0:
            if not self.servicos:
                self.servicos = encargos
            else:
                self.servicos += encargos

        # antes de registrar os novos telefonemas, é necessário apagar os anteriores do mesmo mês
        Telefonema.table.delete(Telefonema.conta_telefone == self).execute()

        # registra os novos telefonemas
        for numero, atributos in telefonemas.iteritems():
            Telefonema(
                numero         = numero,
                conta_telefone = self,
                segundos       = atributos['segundos'],
                quantia        = atributos['quantia'],
                tipo_fone      = atributos['tipo_fone'],
                tipo_distancia = atributos['tipo_distancia']
            )
        self.determinar_responsaveis_telefonemas()


    @property
    def fechamento(self):
        if not hasattr(self, '_fechamento'):
            self._fechamento = self.republica.fechamento_na_data(self.emissao)
        return self._fechamento


    @property
    def total_telefonemas(self):
        return sum(telefonema.quantia for telefonema in self.telefonemas)


    @property
    def total_sem_dono(self):
        return sum(telefonema.quantia for telefonema in self.telefonemas if not telefonema.responsavel)


    @property
    def total_ex_moradores(self):
        return sum(telefonema.quantia for telefonema in self.telefonemas if telefonema.responsavel and (telefonema.responsavel not in self.moradores))

    @property
    def moradores(self):
        if not hasattr(self, '_moradores'):
            self._moradores = set(self.republica.moradores(self.fechamento.data_inicial, self.fechamento.data_final))
        return self._moradores

    @property
    def ex_moradores(self):
        return set([telefonema.responsavel for telefonema in self.telefonemas \
                    if telefonema.responsavel and telefonema.responsavel not in self.moradores])

    @property
    def participantes(self):
        return set.union(self.moradores, self.ex_moradores)


    @property
    def total(self):
        return self.servicos + (self.franquia if self.franquia >= self.total_telefonemas else self.total_telefonemas)


class Telefonema(Entity):
    numero         = Field(Numeric(12, 0), primary_key = True)
    tipo_fone      = Field(Integer,        required = True) # fixo, celular, net fone
    tipo_distancia = Field(Integer,        required = True) # Local, DDD, DDI
    segundos       = Field(Integer,        required = True)
    quantia        = Field(Numeric(10, 2),   required = True)
    responsavel    = ManyToOne('Pessoa')
    conta_telefone = ManyToOne('ContaTelefone', ondelete = 'cascade', primary_key = True)





class TipoDespesa(Entity):
    nome = Field(Unicode(40), required = True)
    descricao = Field(Unicode)
    republica = ManyToOne('Republica',  required = True)

    using_options(tablename = 'tipo_despesa')

    def __repr__(self):
        return '<nome:%s>' % self.nome


class Despesa(Entity):
    data = Field(Date, default = date.today, required = True)
    quantia = Field(Numeric(10, 2), required = True)
    responsavel = ManyToOne('Pessoa', required = True)
    tipo = ManyToOne('TipoDespesa', required = True)


    @classmethod
    def get_despesas_no_periodo(cls, data_inicial, data_final = None, pessoa = None, republica = None):
        # TODO: Alguma situação de busca sem definir nem pessoa nem república?
        #if not (pessoa or republica):
        #   raise Exception???

        # monta as cláusulas que serão usadas na pesquisa das despesas
        DespesaAgendada.cadastrar_despesas_agendadas()
        if not data_final:
            clausula_data = (Despesa.data == data_inicial)
        else:
            data_final = max(data_inicial, data_final)
            clausula_data = and_(Despesa.data >= data_inicial, Despesa.data <= data_final)
        clausula_pessoa = (Despesa.responsavel == pessoa) if pessoa else None
        clausula_republica = and_(Despesa.tipo_id == TipoDespesa.id, TipoDespesa.republica == republica) if republica else None

        return Despesa.query.filter(
                and_(
                    clausula_data,
                    clausula_pessoa,
                    clausula_republica
                    )
            ).all()



class DespesaAgendada(Entity):
    proximo_vencimento = Field(Date, required = True)
    data_termino = Field(Date)
    quantia = Field(Numeric(10,2), required = True)
    responsavel = ManyToOne('Pessoa', required = True)
    tipo = ManyToOne('TipoDespesa', required = True)

    using_options(tablename = 'despesa_agendada')

    def __repr__(self):
        return 'DespesaAgendada <tipo: %r, proximo_vencimento: %r, data_termino: %r, responsavel: %r, quantia: %r>' % \
                (self.tipo, self.proximo_vencimento, self.data_termino, self.responsavel, self.quantia)



    @classmethod
    def cadastrar_despesas_agendadas(cls):
        '''
        O cadastro é feito para todas as despesas agendadas, independente de pessoa ou república. Deve ser chamado antes de qualquer
        consulta a despesas no período. Uma vez cadastrado para um dia, uma segunda chamada a essa rotina não vai precisar
        cadastrar mais nada.

        Elimina a necessidade de um cron job pra fazer o serviço de cadastro diário
        '''
        hoje = date.today()
        despesas_agendadas = DespesaAgendada.query.filter(DespesaAgendada.proximo_vencimento <= hoje).all()
        log.debug('DespesaAgendada.cadastrar_despesas_agendadas(): %r' % despesas_agendadas)
        if not despesas_agendadas:
            return
        for despesa in despesas_agendadas:
            data_ref = hoje if not despesa.data_termino else min(despesa.data_termino, hoje)
            log.debug('DespesaAgendada.cadastrar_despesas_agendadas: Cadastrar %r até %r' % (despesa, data_ref))
            while despesa.proximo_vencimento <= data_ref:
                nova_despesa = Despesa(
                        data        = despesa.proximo_vencimento,
                        quantia     = despesa.quantia,
                        responsavel = despesa.responsavel,
                        tipo        = despesa.tipo
                    )
                despesa.proximo_vencimento += relativedelta(months = 1)
            if despesa.data_termino and despesa.data_termino < despesa.proximo_vencimento:
                log.debug('DespesaAgendada.cadastrar_despesas_agendadas: Excluir %r. Fim do prazo' % despesa)
                despesa.delete()
        # TODO: verficar se dá pra salvar só esse objeto sem comprometer toda a sessão.
        Session.commit() # novas despesas e também a despesa_agendada com próximo vencimento atualizado


