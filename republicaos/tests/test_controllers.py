import turbogears
from nose import with_setup
from turbogears import testutil
from republicaos.controllers import Root
import cherrypy

def teardown_func():
    """Tests for apps using identity need to stop CP/TG after each test to
    stop the VisitManager thread. See http://trac.turbogears.org/turbogears/ticket/1217
    for details.
    """
    turbogears.startup.stopTurboGears()

cherrypy.root = Root()

#def test_method():
    #"the index method should return a string called now"
    #import types
    #result = testutil.call(cherrypy.root.index)
    #assert type(result["now"]) == types.StringType
#test_method = with_setup(teardown=teardown_func)(test_method)

#def test_indextitle():
    #"The indexpage should have the right title"
    #testutil.createRequest("/")
    #response = cherrypy.response.body[0].lower() 
    #assert "<title>welcome to turbogears</title>" in response
#test_indextitle = with_setup(teardown=teardown_func)(test_indextitle)

#def test_logintitle():
    #"login page should have the right title"
    #testutil.createRequest("/login")
    #response = cherrypy.response.body[0].lower()
    #assert "<title>login</title>" in response
#test_logintitle = with_setup(teardown=teardown_func)(test_logintitle)
