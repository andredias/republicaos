from elixir      import Unicode, Date, DateTime, Time, String, Integer, Numeric
from elixir      import Entity, has_field, using_options, using_table_options, using_mapper_options
from elixir      import has_many as one_to_many
from elixir      import belongs_to as many_to_one
from elixir      import has_and_belongs_to_many as many_to_many
from elixir      import metadata
from sqlalchemy  import ForeignKey, ForeignKeyConstraint
from datetime    import datetime

metadata.connect( 'sqlite:///' )
metadata.engine.echo = True

class Pessoa( Entity ):
    has_field( 'nome', Unicode( 80 ), nullable = False, unique = True )
    using_options( tablename = 'pessoa' )
    one_to_many( 'contatos', of_kind = 'Contato', inverse = 'pessoa' )
    one_to_many( 'responsavel_por_telefones', of_kind = 'ResponsavelPorTelefone', inverse = 'responsavel' )

class Contato( Entity ):
    has_field( 'contato', String( 100 ), nullable = False ),
    has_field( 'tipo', Integer, nullable = False ),
    many_to_one( 'pessoa', of_kind = 'Pessoa', inverse = 'contatos' )
    using_options( tablename = 'contato' )

class ResponsavelPorTelefone( Entity ):
    has_field( 'telefone', Integer, primary_key = True )
    has_field( 'descricao', Unicode )
    using_options( tablename = 'responsavel_telefone' )
    many_to_one( 'responsavel', of_kind = 'Pessoa',
	    inverse = 'responsavel_por_telefones', colname = 'id_pessoa_resp',
	    column_kwargs = dict( primary_key = True ))

class Republica( Entity ):
    has_field( 'nome', Unicode( 80 ), nullable = False )
    has_field( 'data_criacao', Date, default = datetime.now, nullable = False )
    has_field( 'logradouro', Unicode( 150 ))
    has_field( 'complemento', Unicode( 100 ))
    has_field( 'bairro', Unicode( 100 ))
    has_field( 'cidade', Unicode( 80 ))
    has_field( 'uf', String( 2 ))
    has_field( 'cep', String( 8 ))
    using_options( tablename = 'republica' )
    one_to_many( 'fechamentos', of_kind = 'Fechamento', inverse = 'republica' )
    one_to_many( 'contas_telefone', of_kind = 'ContaTelefone', inverse = 'republica' )
    one_to_many( 'tipos_despesa', of_kind = 'TipoDespesa', inverse = 'republica' )
    
    def moradores( data_inicial = None, data_final = datetime.now() ):
	    pass

class Fechamento( Entity ):
    has_field( 'data', Date, primary_key = True )
    using_options( tablename = 'fechamento' )
    many_to_one( 'republica', of_kind = 'Republica', inverse = 'fechamentos', colname = 'id_republica',
	    column_kwargs = dict( primary_key = True ))

class ContaTelefone( Entity ):
    has_field( 'companhia', Integer, nullable = False )
    has_field( 'telefone', Integer, nullable = False )
    has_field( 'dia_vencimento', Integer, nullable = False )
    using_options( tablename = 'conta_telefone' )
    many_to_one( 'republica', of_kind = 'Republica', inverse = 'contas_telefone',
	    column_kwargs = dict( nullable = False ))
#    one_to_many( 'telefonemas', of_kind = 'Telefonema', inverse = 'conta_telefone' )
    def telefonemas( periodo ):
	    pass

class Telefonema( Entity ):
    has_field( 'periodo_ref', Integer, primary_key = True )
    has_field( 'telefone', Integer, primary_key = True )
    has_field( 'tipo_fone', Integer, nullable = False )			# fixo, celular, net fone
    has_field( 'tipo_distancia', Integer, nullable = False )	# Local, DDD, DDI
    has_field( 'duracao', Time, nullable = False )
    has_field( 'valor', Numeric( 8, 2 ), nullable = False )
    using_options( tablename = 'telefonema' )
    many_to_one( 'responsavel', of_kind = 'Pessoa', inverse = 'telefonemas')
    many_to_one( 'conta_telefone', of_kind = 'ContaTelefone', inverse = 'telefonemas',
	    colname = 'id_conta_telefone', column_kwargs = dict( primary_key = True ))

class Morador( Entity ):
    has_field( 'data_entrada', Date, default = datetime.now, primary_key = True )
    has_field( 'data_saida', Date )
    using_options( tablename = 'morador' )
    many_to_one( 'republica', of_kind = 'Republica', inverse = 'moradores', colname = 'id_republica',
	    column_kwargs = dict( primary_key = True ))
    many_to_one( 'pessoa', of_kind = 'Pessoa', colname = 'id_pessoa',
	    column_kwargs = dict( primary_key = True ))

class TipoDespesa( Entity ):
    has_field( 'tipo', Unicode(40), nullable = False )
    has_field( 'descricao', String )
    using_options( tablename = 'tipo_despesa' )
    many_to_one( 'republica', of_kind = 'Republica', inverse = 'tipo_despesas',
		column_kwargs = dict( nullable = False ))


class Despesa( Entity ):
    has_field( 'data', Date, default = datetime.now, nullable = False )
    has_field( 'valor', Numeric( 8, 2 ), nullable = False )
    using_options( tablename = 'despesa' )
    many_to_one( 'pessoa', of_kind = 'Pessoa', column_kwargs = dict( nullable = False ))
    many_to_one( 'republica', of_kind = 'Republica', column_kwargs = dict( nullable = False ))
    many_to_one( 'tipo_despesa', of_kind = 'TipoDespesa', column_kwargs = dict( nullable = False ))
