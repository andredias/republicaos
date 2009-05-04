# -*- coding: utf-8 -*-

from elixir      import Unicode, Boolean, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, using_options, using_table_options, using_mapper_options
from elixir      import Field, OneToMany, ManyToOne
from sqlalchemy  import types, and_, or_, select, UniqueConstraint, func
from datetime    import date, datetime, time
import csv
import elixir
from decimal     import Decimal
from dateutil.relativedelta import relativedelta

elixir.options_defaults['shortnames'] = True

def float_equal(float1, float2, precision = 0.001):
    return abs(float(float1) - float(float2)) < precision

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
    nome     = Field(Unicode(80), required = True, unique = True)
    contatos = OneToMany('Contato', order_by = 'contato')
    using_options(order_by = 'nome')
    
    def get_emails():
        pass
    
    def get_telefones_contato():
        pass
    
    def __repr__(self):
        return "<nome:'%s'>" % self.nome.encode('utf-8')









class Contato(Entity):
    contato = Field(Unicode(100), required = True)
    pessoa  = ManyToOne('Pessoa', colname = 'id_pessoa', required = True)
    
    def __repr__(self):
        return '<contato:%s, pessoa:%s>' % (self.contato.encode('utf-8'), self.pessoa.nome.encode('utf-8'))










class TelefoneRegistrado(Entity):
    '''
    TelefoneRegistrado registrado na república tendo algum morador como responsável.
    
    Não poderá haver mais de um morador sendo responsável pelo telefone em uma república. Essa restrição
    é reforçada pela chave primária.
    '''
    numero      = Field(Numeric(12, 0), primary_key = True)
    descricao   = Field(Unicode)
    republica   = ManyToOne('Republica', colname = 'id_republica', primary_key = True)
    responsavel = ManyToOne('Morador', colname = 'id_morador', required = True)
    using_options(tablename = 'telefone')
    
    def __repr__(self):
        return "<número: %d, república: '%s', responsável: '%s'>" % (self.numero, self.republica.nome.encode('utf-8'), self.responsavel.pessoa.nome.encode('utf-8'))







class Republica(Entity):
    nome         = Field(Unicode(90), required = True)
    data_criacao = Field(Date, default = date.today, required = True)
    logradouro   = Field(Unicode(150))
    complemento  = Field(Unicode(100))
    cidade       = Field(Unicode(80))
    uf           = Field(String(2))
    cep          = Field(String(8))
    fechamentos           = OneToMany('Fechamento', order_by = '-data')
    tipos_despesa         = OneToMany('TipoDespesa', order_by = 'nome')
    telefones_registrados = OneToMany('TelefoneRegistrado', order_by = 'numero')
    alugueis              = OneToMany('Aluguel', order_by = '-data_cadastro')
    
    
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
        return Fechamento(data = data, republica = self)
    
    
    def moradores(self, data_inicial = None, data_final = None):
        '''
        Retorna os moradores da república no período de tempo
        '''
        moradores =  Morador.query.filter(
                        and_(
                            Morador.id_republica == self.id,
                            Morador.data_entrada < data_final,
                            or_(Morador.data_saida >= data_inicial, Morador.data_saida == None)
                        )
                    ).all()
        moradores.sort(key = lambda obj: obj.pessoa.nome)
        return moradores
    
    
    def contas_telefone(self, data_inicial, data_final):
        '''
        Retorna as contas de telefone da república no período
        '''
        return ContaTelefone.query.filter(
                    and_(
                        ContaTelefone.id_republica == self.id,
                        ContaTelefone.emissao >= data_inicial,
                        ContaTelefone.emissao <= data_final
                    )
                ).all()
    
    
    def aluguel(self, data):
        for aluguel in self.alugueis:
            if aluguel.data_cadastro <= data:
                return aluguel.valor
        
        return None
    
    
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




class Aluguel(Entity):
    valor = Field(Money(10, 2), required = True)
    data_cadastro = Field(Date, primary_key = True)
    republica = ManyToOne('Republica',  colname = 'id_republica', primary_key = True)



class PesoQuota(Entity):
    peso_quota    = Field(Money(10,2), required = True)
    data_cadastro = Field(Date, primary_key = True)
    morador       = ManyToOne('Morador', colname = 'id_morador', primary_key = True)
    using_options(tablename = 'peso_quota')
    
    def __repr__(self):
        return "<peso_quota: %s, %s, %s>" % (self.morador.pessoa.nome.encode('utf-8'), self.peso_quota, self.data_cadastro)



class Intervalo(object):
    def __init__(self, data_inicial, data_final, fechamento):
        assert data_inicial < data_final
        
        self.data_inicial = data_inicial
        self.data_final   = data_final
        self.fechamento   = fechamento
        
        self.participantes = [participante for participante in fechamento.participantes if participante.data_entrada < data_final \
                            and (not participante.data_saida or data_inicial <= participante.data_saida)]
        self.total_peso_quota  = sum(participante.peso_quota(data_inicial) for participante in self.participantes)
        self.num_dias          = (data_final - data_inicial).days if len(self.participantes) else 0
        fechamento._total_dias += self.num_dias
    
    
    def quota_peso(self, participante):
        if (not self.total_peso_quota) or (participante not in self.participantes):
            return 0
        return self._razao_num_dias() * participante.peso_quota(self.data_inicial) / self.total_peso_quota
    
    
    def quota(self, participante):
        if (not self.participantes) or (participante not in self.participantes):
            return 0
        return self._razao_num_dias() / len(self.participantes)
    
    
    def _razao_num_dias(self):
        if not self.fechamento.total_dias:
            return 0
        return Decimal(str(100.0 * self.num_dias / self.fechamento.total_dias))
    
    
    
class Fechamento(Entity):
    data      = Field(Date, primary_key = True)
    republica = ManyToOne('Republica', colname = 'id_republica', primary_key = True)
    
    def __repr__(self):
        return "<fechamento:%s [%s, %s], república:'%s'>" % \
            (
            self.data.strftime('%d/%m/%Y'),
            self.data_inicial.strftime('%d/%m/%Y'),
            self.data_final.strftime('%d/%m/%Y'),
            self.republica.nome.encode('utf-8')
            )
    
    
    @property
    def contas_telefone(self):
        if not hasattr(self, '_contas_telefone'):
            self._contas_telefone = self.republica.contas_telefone(self.data_inicial, self.data_final)
        return self._contas_telefone
    
    
    @property
    def moradores(self):
        if not hasattr(self, '_moradores'):
            self._moradores = self.republica.moradores(self.data_inicial, self.data_final)
        return self._moradores
    
    
    @property
    def ex_moradores(self):
        if not hasattr(self, '_ex_moradores'):
            self._ex_moradores = set()
            for conta in self.contas_telefone:
                self._ex_moradores.update(conta.ex_moradores)
            self._ex_moradores = list(self._ex_moradores)
            self._ex_moradores.sort(key = lambda obj:obj.pessoa.nome)
        return self._ex_moradores
        
    
    @property
    def participantes(self):
        if not hasattr(self, '_participantes'):
            self._participantes = self.moradores + self.ex_moradores
            self._participantes.sort(key = lambda obj:obj.pessoa.nome)
        return self._participantes
            
    
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
    
    
    @property
    def total_dias(self):
        if not hasattr(self, '_total_dias'):
            self._calcular_quotas_participantes()
        return self._total_dias
    
    
    def quota(self, participante):
        if not hasattr(self, 'intervalos'):
            self._calcular_quotas_participantes()
        return sum(intervalo.quota(participante) for intervalo in self.intervalos)
    
    
    def quota_peso(self, participante):
        if not hasattr(self, 'intervalos'):
            self._calcular_quotas_participantes()
        return sum(intervalo.quota_peso(participante) for intervalo in self.intervalos)
    
    
    def _calcular_quotas_participantes(self):
        # Definição dos intervalos
        # todas as datas de entrada e saída formam os intervalos do período
        datas = set()
        for participante in self.moradores:
            data_inicial = max(participante.data_entrada, self.data_inicial)
            # soma-se um dia à data final pois conta-se apenas dia vencido no cálculo.
            data_final   = min(self.data_final, participante.data_saida if participante.data_saida else self.data_final) + relativedelta(days = 1)
            datas.add(data_inicial)
            datas.add(data_final)
        
        # se a mudança na peso_quota do aluguel do participante devesse ser considerado no meio do período,
        # os intervalos também deveriam considerar as datas das mudança, incluindo-as no conjunto datas aqui
            
        datas = list(datas)
        datas.sort()
        self._total_dias = 0 # vai ser usado pelo Intervalo
        self.intervalos  = list()
        for i in range(len(datas) - 1):
            novo_intervalo = Intervalo(datas[i], datas[i+1], self)
            self.intervalos.append(novo_intervalo)
    
    
    def despesas(self, participante = None):
        if not hasattr(self, '_despesas'):
            self._despesas = Despesa.query.filter(
                    and_(
                        Morador.id_republica == self.republica.id,
                        Morador.id           == Despesa.id_morador,
                        Despesa.data         >= self.data_inicial,
                        Despesa.data         <= self.data_final
                        )).order_by(Despesa.data).all()
        return self._despesas if not participante else [despesa for despesa in self._despesas if despesa.responsavel is participante]
    
    
    def total_despesas(self, participante = None):
        return sum(despesa.quantia for despesa in self.despesas(participante))
    
    
    def rateio(self, participante):
        return (self.total_despesas() - self.total_telefone()) * self.quota(participante) / Decimal(100)
    
    
    def saldo_final(self, participante):
        return self.rateio(participante) + self.total_telefone(participante) - self.total_despesas(participante)
    
    
    def total_telefone(self, participante = None):
        if not participante:
            return sum(conta.total for conta in self.contas_telefone)
        else:
            return sum(conta.rateio.a_pagar(participante) for conta in self.contas_telefone)
        
    @property
    def total_tipo_despesa(self):
        if not hasattr(self, '_total_tipo_despesa'):
            self._total_tipo_despesa = dict(
                [(tipo_despesa, sum(despesa.quantia for despesa in self.despesas() if despesa.tipo == tipo_despesa))
                for tipo_despesa in self.republica.tipos_despesa]
            )
            for tipo, total in self.total_tipo_despesa.items():
                if not total:
                    self.total_tipo_despesa.pop(tipo)
        return self._total_tipo_despesa
    
    
    @property
    def acerto_a_pagar(self):
        if not hasattr(self, '_acerto_a_pagar'):
            self._executar_acerto_final()
        return self._acerto_a_pagar
    
    
    @property
    def acerto_a_receber(self):
        if not hasattr(self, '_acerto_a_receber'):
            self._executar_acerto_final()
        return self._acerto_a_receber
    
    
    def _executar_acerto_final(self):
        '''
        Executa o acerto final das contas, determinando quem deve pagar o que pra quem. A ordem dos credores
        e devedores é ordenada para que sempre dê a mesma divisão.
        '''
        credores  = [participante for participante in self.participantes if self.saldo_final(participante) < 0]
        devedores = [participante for participante in self.participantes if self.saldo_final(participante) > 0]
        
        # ordena a lista de credores e devedores de acordo com o saldo_final
        credores.sort(key =  lambda obj: (self.saldo_final(obj), obj.pessoa.nome))
        devedores.sort(key = lambda obj: (self.saldo_final(obj), obj.pessoa.nome), reverse = True)
        
        self._acerto_a_pagar   = dict([(devedor, dict()) for devedor in devedores])
        self._acerto_a_receber = dict([(credor, dict()) for credor in credores])
        if len(devedores) == 0: return
        
        devedores = iter(devedores)
        try:
            devedor     = devedores.next()
            saldo_pagar = self.saldo_final(devedor)
            for credor in credores:
                saldo_receber = abs(self.saldo_final(credor))
                while (saldo_receber > 0):
                        if saldo_receber >= saldo_pagar:
                            self._acerto_a_pagar[devedor][credor] = saldo_pagar
                            saldo_receber -= saldo_pagar
                            devedor        = devedores.next()
                            saldo_pagar    = self.saldo_final(devedor)
                        else:
                            self._acerto_a_pagar[devedor][credor] = saldo_receber
                            saldo_pagar  -= saldo_receber
                            saldo_receber = 0
        except StopIteration:
            pass
        
        for devedor in self._acerto_a_pagar.keys():
            for credor in self._acerto_a_pagar[devedor].keys():
                self._acerto_a_receber[credor][devedor] = self._acerto_a_pagar[devedor][credor]
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
    vencimento   = Field(Date, required = True)
    emissao      = Field(Date, required = True)
    telefone     = Field(Numeric(12, 0), required = True)
    id_operadora = Field(Integer, required = True)
    franquia     = Field(Money(10,2), default = 0)
    servicos     = Field(Money(10,2), default = 0)
    republica    = ManyToOne('Republica', colname = 'id_republica', required = True)
    telefonemas  = OneToMany('Telefonema', order_by = 'numero')
    
    using_options(tablename = 'conta_telefone')
    using_table_options(UniqueConstraint('telefone', 'emissao'))
    
    def __repr__(self):
        return '<telefone: %d, emissão: %s, república: %s>' % \
                (self.telefone, self.emissao.strftime('%d/%m/%Y'), self.republica.nome.encode('utf-8'))
    
    
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
        
        # antes de registrar os novos telefonemas, é necessário apagar os anteriores do mesmo mês
        Telefonema.table.delete(Telefonema.id_conta_telefone == self.id).execute()
        
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
    quantia        = Field(Money(10, 2),   required = True)
    responsavel    = ManyToOne('Morador',       colname = 'id_morador')
    conta_telefone = ManyToOne('ContaTelefone', colname = 'id_conta_telefone', ondelete = 'cascade', primary_key = True)
    
    def __repr__(self):
        return "<número:%d, quantia:%s, segundos:%s, responsável:'%s'>" % \
            (self.numero, self.quantia, self.segundos, (self.responsavel.pessoa.nome.encode('utf-8') if self.responsavel else ''))


class Morador(Entity):
    data_entrada = Field(Date, default = date.today, required = True)
    data_saida   = Field(Date)
    despesas_periodicas = OneToMany('DespesaPeriodica', order_by = 'proximo_vencimento')
    telefones_sob_responsabilidade = OneToMany('TelefoneRegistrado')
    republica    = ManyToOne('Republica', colname = 'id_republica', required = True)
    pessoa       = ManyToOne('Pessoa',    colname = 'id_pessoa', required = True)
    pesos_quota  = OneToMany('PesoQuota', order_by = '-data_cadastro')
    
    using_table_options(UniqueConstraint('id_pessoa', 'id_republica', 'data_entrada'))
    
    def __repr__(self):
        return "<pessoa:'%s', república:'%s', data_entrada:%s>" % \
            (self.pessoa.nome.encode('utf-8'), self.republica.nome.encode('utf-8'), self.data_entrada.strftime('%d/%m/%Y'))
    
    
    def _get_despesas(self, data_inicial, data_final):
        return Despesa.query.filter(
                    and_(
                        Despesa.id_morador == self.id,
                        Despesa.data       >= data_inicial,
                        Despesa.data       <= data_final
                        )
                    ).order_by(Despesa.data).all()
    
    
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
                despesa.proximo_vencimento += relativedelta(months = 1)
                
            if despesa.data_termino and \
                ((despesa.data_termino < data_final) or
                 (despesa.data_termino < despesa.proximo_vencimento)):
                despesa.delete()
    
    
    def despesas(self, data_inicial, data_final):
        self._cadastrar_despesas_periodicas(data_inicial, data_final)
        return self._get_despesas(data_inicial, data_final)
    
    
    def despesas_por_tipo(self, tipo_despesa, data_inicial = None, data_final = None):
        return [despesa for despesa in self.despesas(data_inicial, data_final) if despesa.tipo == tipo_despesa]
    
    
    def telefonemas(self, conta_telefone):
        if conta_telefone.republica is not self.republica:
            return None
        return Telefonema.query.filter(
                    and_(
                        Telefonema.id_conta_telefone == conta_telefone.id,
                        Telefonema.id_morador == self.id
                        )
                    ).order_by(Telefonema.numero).all()
    
    
    def qtd_dias_morados(self, data_inicial = None, data_final = None):
        entrada  = max(self.data_entrada, data_inicial)
        saida    = min(self.data_saida, data_final) if self.data_saida else data_final
        qtd_dias = (saida - entrada).days + 1
        return (qtd_dias if qtd_dias >= 0 else 0)
    
    
    def peso_quota(self, data):
        '''Qual o peso_quota do morador em uma determinada data'''
        
        for peso_quota in self.pesos_quota:
            if peso_quota.data_cadastro <= data:
                return peso_quota.peso_quota
        
        # se chegou aqui, não há nenhum peso_quota cadastrada
        # dividir igualmente entre os moradores cadastrados no período
        
        num_moradores = select(
                        [func.count('*')],
                        from_obj = [Morador.table],
                        whereclause = and_(
                            Morador.id_republica == self.id_republica,
                            Morador.data_entrada <= data,
                            or_(Morador.data_saida >= data, Morador.data_saida == None)
                            )
                        ).execute().fetchone()[0]
        
        return Decimal(str(100.0 / num_moradores) if num_moradores else 0)






class TipoDespesa(Entity):
    nome = Field(Unicode(40), required = True)
    descricao = Field(Unicode)
    republica = ManyToOne('Republica',  required = True)
    
    using_options(tablename = 'tipo_despesa')
    
    def __repr__(self):
        return '<nome:%s>' % self.nome.encode('utf-8')


class Despesa(Entity):
    data        = Field(Date, default = date.today, required = True)
    quantia     = Field(Money(10, 2), required = True)
    responsavel = ManyToOne('Morador',     colname = 'id_morador',      required = True)
    tipo        = ManyToOne('TipoDespesa', colname = 'id_tipo_despesa', required = True)
    
    def __repr__(self):
        return '<data:%s, quantia:%s, tipo:%s, responsável:%s>' % \
            (self.data.strftime('%d/%m/%Y'), self.quantia, self.tipo.nome.encode('utf-8'), self.responsavel.pessoa.nome.encode('utf-8'))


class DespesaPeriodica(Entity):
    proximo_vencimento = Field(Date, default = date.today, required = True)
    quantia            = Field(Money(10,2), required = True)
    data_termino       = Field(Date)
    responsavel        = ManyToOne('Morador',     colname = 'id_morador',      required = True)
    tipo               = ManyToOne('TipoDespesa', colname = 'id_tipo_despesa', required = True)
    
    using_options(tablename = 'despesa_periodica')
    
    def __repr__(self):
        return "<próximo_vencimento:%s, data_termino:%s, quantia:%s, tipo:'%s', responsável:'%s'>" % \
            (self.proximo_vencimento.strftime('%d/%m/%Y'), (self.data_termino.strftime('%d/%m/%Y') if self.data_termino else ''), self.quantia, self.tipo.nome.encode('utf-8'), self.responsavel.pessoa.nome.encode('utf-8'))
