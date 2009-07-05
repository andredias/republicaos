from republicaos.tests import *
from republicaos.tests import Session, metadata

class TestElixir(TestModel):
    def setUp(self):
        TestModel.setUp(self)

    def test_metadata(self):
        assert 'A collection of Tables and their associated schema constructs.' in metadata.__doc__

    def test_session(self):
        assert Session.connection().dialect.name is 'sqlite'
    

    def test_model_ops(self):
        import datetime
        g = Session.query(model.Group).filter_by(
                    name=u"Administrators").all()
        assert len(g) == 1
        assert g[0].name == "Administrators"
        u = Session.query(model.User).filter_by(username=u"admin").all()
        assert len(u) == 1
        assert u[0].username == 'admin'
        groups = Session.query(model.Group).all()
        group = Session.query(model.Group).get(2)
        print(group)
        print(list(groups))
        assert group.name == u'Subscription Members'
        u = Session.query(model.User).all()
        assert len(u) == 2
        print(group.permissions)
        assert len(group.permissions) == 1
            
