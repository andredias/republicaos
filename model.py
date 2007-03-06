from sqlalchemy import *

db       = create_engine( 'sqlite:///republique.db' )
metadata = BoundMetaData( db )

pessoa_table = Table( 'pessoa', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'nome', String( 80 ), nullable = False )
)

contato_table = Table('contato', metadata,
	Column( 'id_pessoa', Integer, ForeignKey( 'pessoa.id' ), primary_key = True ),
	Column( 'id_contato', Integer, primary_key = True ),
	Column( 'contato', String( 100 ), nullable = False ),
	Column( 'tipo_contato', Integer, nullable = False )
)

responsavel_telefonema_table = Table( 'responsavel_telefonema', metadata,
	Column( 'id_pessoa', Integer, primary_key = True ),
	Column( 'telefone', String( 12 ), primary_key = True ),
	Column( 'descricao', String ),
	ForeignKeyConstraint( ['id_pessoa'], ['pessoa.id'] )
)

republica_table = Table( 'republica', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'nome', String( 80 ), nullable = False ),
	Column( 'data_criacao', Date, default = func.now(), nullable = False ),
	Column( 'ult_fechamento', Date ),
	Column( 'prox_fechamento', Date )
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
	Column( 'id_republica', Integer, ForeignKey( 'republica.id' )),
	Column( 'tipo', String(40), nullable = False ),
	Column( 'descricao', String )
)

despesa_table = Table( 'despesa', metadata,
	Column( 'id', Integer, primary_key = True ),
	Column( 'data', Date, default = func.now(), nullable = False ),
	Column( 'valor', Numeric( 8, 2 ), nullable = False ),
	Column( 'id_republica', Integer, ForeignKey( 'republica.id' ), nullable = False ),
	Column( 'id_pessoa', Integer, ForeignKey( 'pessoa.id' ), nullable = False ),
	Column( 'id_tipo_despesa', Integer, ForeignKey( 'tipo_despesa.id' ), nullable = False )
)

