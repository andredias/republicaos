import model_elixir
from sqlalchemy import create_engine

class TestaModelo( object ):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()

    def tear_down(self):
	    cleanup_all()
	    
    def test_populando(self):
	    p1 = Pessoa( nome = 'Felipe' )
	   
	    
