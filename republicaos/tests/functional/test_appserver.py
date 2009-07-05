from republicaos.tests import *

class TestAppServer(TestController):
    def test_index(self):
        response = self.app.get('/')
        # Test response...
        tgt = '''<span style="color:lime">repoze.what and repoze.who for Pylons</span>'''
        assert tgt in response
    
