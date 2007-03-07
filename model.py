from sqlalchemy import *

db       = create_engine( 'sqlite:///republique.db' )
metadata = BoundMetaData( db )
session  = create_session( bind_to = db )

pessoa_table = Table( 'pessoa', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'nome', String( 80 ), nullable = False )
)

contato_table = Table('contato', metadata,
	Column( 'id_contato', Integer, primary_key = True ),
	Column( 'contato', String( 100 ), nullable = False ),
	Column( 'tipo_contato', Integer, nullable = False ),
	Column( 'id_pessoa', Integer, ForeignKey( 'pessoa.id' ), nullable = False )
)

responsavel_telefonema_table = Table( 'responsavel_telefonema', metadata,
	Column( 'id_pessoa', Integer, ForeignKey( 'pessoa.id' ), primary_key = True ),
	Column( 'telefone', String( 12 ), primary_key = True ),
	Column( 'descricao', String )
)

republica_table = Table( 'republica', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'nome', String( 80 ), nullable = False ),
	Column( 'data_criacao', Date, default = func.now(), nullable = False ),
	Column( 'logradouro', String( 150 )),
	Column( 'complemento', String( 100 )),
	Column( 'bairro', String( 100 )),
	Column( 'cidade', String( 80 )),
	Column( 'uf', String( 2 )),
	Column( 'cep', String( 8 ))
)

fechamento_table = Table( 'fechamento', metadata,
    Column( 'id_republica', Integer, ForeignKey( 'republica.id' ), primary_key = True ),
    Column( 'data', Date, primary_key = True )
)

conta_telefone_table = Table( 'conta_telefone', metadata, 
	Column( 'id', Integer, primary_key = True ),
	Column( 'id_republica', Integer, ForeignKey( 'republica.id' ), nullable = False ),
	Column( 'companhia', Integer, nullable = False ),
	Column( 'telefone', String( 12 ), nullable = False )
)

telefonema_table = Table( 'telefonema', metadata,
	Column( 'id_conta_telefone', Integer, ForeignKey( 'conta_telefone.id' ), primary_key = True ),
	Column( 'periodo_ref', Integer, primary_key = True ),
	Column( 'telefone', String( 12 ), primary_key = True ),
	Column( 'duracao', Time, nullable = False ),
	Column( 'valor', Numeric( 8, 2 ), nullable = False ),
	Column( 'id_pessoa_resp', Integer, ForeignKey( 'pessoa.id' ))
)

morador_table = Table( 'morador', metadata,
	Column( 'id_republica', Integer, ForeignKey( 'republica.id' ), primary_key = True ),
	Column( 'id_pessoa', Integer, ForeignKey( 'pessoa.id' ), primary_key = True ),
	Column( 'data_entrada', Date, default = func.now(), primary_key = True ),
	Column( 'data_saida', Date )
)

tipo_despesa_table = Table( 'tipo_despesa', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'id_republica', Integer, ForeignKey( 'republica.id' ), nullable = False),
	Column( 'tipo', String(40), nullable = False ),
	Column( 'descricao', String )
)

# manter id_republica na tabela para facilitar a busca
despesa_table = Table( 'despesa', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'data', Date, default = func.now(), nullable = False ),
	Column( 'valor', Numeric( 8, 2 ), nullable = False ),
	Column( 'id_republica', Integer, nullable = False ),
	Column( 'id_pessoa', Integer, ForeignKey( 'pessoa.id' ), nullable = False ),
	Column( 'id_tipo_despesa', Integer, nullable = False ),
	ForeignKeyConstraint(
	    ['id_tipo_despesa', 'id_republica'],
	    ['tipo_despesa.id', 'tipo_despesa.id_republica']
	)
)


#
# ORM
#

from sqlalchemy.orm import *


class Pessoa(object):
    pass

class Contato(object):
    pass

class ResponsavelTelefonema(object):
    pass

class Republica(object):
    pass

class Fechamento(object):
    pass

class ContaTelefone(object):
    pass

class Telefonema(object):
    pass

class Morador(object):
    pass

class TipoDespesa(object):
    pass

class Despesa(object):
    pass


#
# Mappers
#

mapper( Pessoa, pessoa_table )
mapper( Republica, republica_table )

mapper( Contato, contato_table,
    properties = { 
		'pessoa':relation( Pessoa, backref = backref( 'contatos', cascade='all, delete-orphan' ))
	}
)

mapper( ResponsavelTelefonema, responsavel_telefonema_table, properties = { 
    'pessoa':relation( Pessoa, backref = backref( 'resp_por_telefones', cascade='all, delete-orphan' ))
	}
)

mapper( Fechamento, fechamento_table, properties = {
    'republica':relation( Republica, backref = backref( 'fechamentos', cascade='all, delete-orphan' ))
	}
)

mapper( TipoDespesa, tipo_despesa_table, properties = { 'republica':relation( Republica )})
mapper( ContaTelefone, conta_telefone_table,
    properties = { 'republica':relation( Republica, backref=backref( 'telefone' ))}
)

#mapper( Despesa
#mapper( Telefonema
#mapper( Morador




