from pylons import url
from repozepylons.tests import *

class TestLoginController(TestController):
    def test_login_index(self):
        response = self.app.get(url(controller='login', action='index'))
        assert '<h2>Please log in</h2>' in response
    def test_demo_index(self):
        response = self.app.get(url(controller='demo', action='index'))
        assert response.status_int == 200
    def test_demo_privindex_unauth(self):
        response = self.app.get(url(controller='demo', action='privindex'))
        assert response.status_int == 302
    def test_forced_login(self):
            """
            Anonymous users should be redirected to the login form when they
            request a protected area.
    
            """
            # Requesting a protected area as anonymous:
            resp = self.app.get(url(controller='demo', action='privindex'), 
                                expect_errors=True, status=401)
            assert resp.location.startswith('http://localhost/login')
            # Being redirected to the login page:
            login_page = resp.follow(status=200)
            login_form = login_page.form
            login_form['login'] = 'admin'
            login_form['password'] = 'admin'
            # Submitting the login form:
            login_handler = login_form.submit(status=302)
            # We should be redirected to the post_login page:
            assert login_handler.location == 'http://localhost/login/welcome_back?__logins=0&came_from=http%3A%2F%2Flocalhost%2Fdemo%2Fprivindex'
            # We should be further redirected to the initially requested page:
            welcome_page = login_handler.follow(status=302)
            final_page = welcome_page.follow(status=200)
            # Checking that the user was correctly authenticated:
            assert 'authtkt' in final_page.request.cookies, \
                   "Session cookie wasn't defined: %s" % final_page.request.cookies
            assert 'Authenticated: admin' in final_page


    def test_voluntary_login(self):
            """Voluntary logins should work perfectly"""
            # Requesting the login form:
            login_page = self.app.get('/login/index', status=200)
            login_form = login_page.form
            login_form['login'] = 'admin'
            login_form['password'] = 'admin'
            # Submitting the login form:
            login_handler = login_form.submit(status=302)
            print(login_handler.location)
            assert login_handler.location == 'http://localhost/login/welcome_back?__logins=0&came_from=%2F'
            # Checking that the user was correctly authenticated:
            welcome_page = login_handler.follow(status=302)
            final_page = welcome_page.follow(status=200)
            assert 'authtkt' in final_page.request.cookies, \
                   "Session cookie wasn't defined: %s" % final_page.request.cookies

    def test_logout(self):
            """Users should be logged out correctly"""
            # Logging in:
            self.app.get('/login_handler?login=admin&password=admin', status=302)
            # Checking that the user was correctly authenticated:
            home_page = self.app.get('/', status=200)
            assert 'authtkt' in home_page.request.cookies, \
                   "Session cookie wasn't defined: %s" % home_page.request.cookies
            # Now let's log out:
            self.app.get('/logout_handler', status=302)
            # Finally, let's check that the session cookie was destroyed after logout:
            home_page = self.app.get('/', status=200)
            assert home_page.request.cookies.get('authtkt') == '', \
                   "Session cookie wasn't deleted: %s" % home_page.request.cookies



class TestDemoController(TestProtectedAreasController):
    def test_privindex_as_anonymous(self):
        """Anonymous users must not access the panel"""
        self.app.get('/demo/privindex', status=401)
    
    def test_privindex_as_admin(self):
        """Administrators can access the private index"""
        environ = {'REMOTE_USER': 'admin'}
        resp = self.app.get('/demo/privindex', extra_environ=environ, status=200)
        assert "Authenticated: admin" in resp.body


