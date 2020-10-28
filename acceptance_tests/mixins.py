from django.conf import settings


try:
    from acceptance_tests import auth
except ImportError:
    # Avoid pylint errors when auth doesn't exist
    auth = None


class LoginMixin:
    """ Mixin used for log in through a cookie."""

    def login(self, superuser=False):
        """ Craft cookie to fake a login. """
        assert auth, "auth.py could not be imported from acceptance_tests"

        # First visit a guaranteed 404, just to get selenium in the right domain (it doesn't like us setting cookies
        # for places we aren't in, even if we specify a domain).
        self.driver.get('http://localhost:19150/not-a-place')

        self.driver.add_cookie({
            'name': settings.SESSION_COOKIE_NAME,
            'value': auth.SESSION_SUPER_KEY if superuser else auth.SESSION_KEY,
            'secure': False,
            'path': '/',
        })

        self.driver.refresh()
