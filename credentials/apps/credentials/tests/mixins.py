"""
Mixins for use during testing.
"""
import json

from django.conf import settings
import httpretty


CONTENT_TYPE = 'application/json'


class ProgramsDataMixin(object):
    """ Mixin mocking Programs API URLs and providing fake data for testing."""
    PROGRAM_NAMES = [
        'Test Program A',
        'Test Program B',
    ]

    COURSE_KEYS = [
        'organization-a/course-a/fall',
        'organization-a/course-a/winter',
        'organization-a/course-b/fall',
        'organization-a/course-b/winter',
        'organization-b/course-c/fall',
        'organization-b/course-c/winter',
        'organization-b/course-d/fall',
        'organization-b/course-d/winter',
    ]

    PROGRAMS_API_RESPONSE = {
        'id': 1,
        'name': PROGRAM_NAMES[0],
        'subtitle': 'A program used for testing purposes',
        'category': 'xseries',
        'status': 'unpublished',
        'marketing_slug': '',
        'organizations': [
            {
                'display_name': 'Test Organization A',
                'key': 'organization-a'
            }
        ],
        'course_codes': [
            {
                'display_name': 'Test Course A',
                'key': 'course-a',
                'organization': {
                    'display_name': 'Test Organization A',
                    'key': 'organization-a'
                },
                'run_modes': [
                    {
                        'course_key': COURSE_KEYS[0],
                        'mode_slug': 'verified',
                        'sku': '',
                        'start_date': '2015-11-05T07:39:02.791741Z',
                        'run_key': 'fall'
                    },
                    {
                        'course_key': COURSE_KEYS[1],
                        'mode_slug': 'verified',
                        'sku': '',
                        'start_date': '2015-11-05T07:39:02.791741Z',
                        'run_key': 'winter'
                    }
                ]
            },
            {
                'display_name': 'Test Course B',
                'key': 'course-b',
                'organization': {
                    'display_name': 'Test Organization A',
                    'key': 'organization-a'
                },
                'run_modes': [
                    {
                        'course_key': COURSE_KEYS[2],
                        'mode_slug': 'verified',
                        'sku': '',
                        'start_date': '2015-11-05T07:39:02.791741Z',
                        'run_key': 'fall'
                    },
                    {
                        'course_key': COURSE_KEYS[3],
                        'mode_slug': 'verified',
                        'sku': '',
                        'start_date': '2015-11-05T07:39:02.791741Z',
                        'run_key': 'winter'
                    }
                ]
            }
        ],
        'created': '2015-10-26T17:52:32.861000Z',
        'modified': '2015-11-18T22:21:30.826365Z'
    }

    def mock_programs_api(self, program_id):
        """ Utility for mocking out Programs API URLs with status code 200."""
        data = self.PROGRAMS_API_RESPONSE
        self._mock_programs_api(program_id, data)

    def mock_programs_api_404(self, program_id):
        """ Utility for mocking out Programs API URLs with status code 404."""
        data = None
        self._mock_programs_api(program_id, data, 404)

    def mock_programs_api_500(self, program_id):
        """ Utility for mocking out Programs API URLs with status code 500."""
        data = None
        self._mock_programs_api(program_id, data, 500)

    def _mock_programs_api(self, program_id, data, status_code=200):
        """ Utility for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        programs_api_url = settings.PROGRAMS_API_URL
        url = '{root}/programs/{program_id}/'.format(root=programs_api_url.strip('/'), program_id=program_id)
        body = json.dumps(data)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, url, body=body, content_type=CONTENT_TYPE, status=status_code)


class OrganizationsDataMixin(object):
    """ Mixin mocking Organizations API URLs and providing fake data for testing."""
    ORGANIZATIONS_API_RESPONSE = {
        'name': 'Test Organization',
        'short_name': 'test-org',
        'description': 'Organization for testing.',
        'logo': 'http://testserver/media/organization_logos/test_org_logo.png',
    }

    def mock_organizations_api(self, organization_key):
        """ Utility for mocking out Organizations API URLs with status code 200."""
        data = self.ORGANIZATIONS_API_RESPONSE
        self._mock_organizations_api(organization_key, data)

    def mock_organizations_api_404(self, organization_key):
        """ Utility for mocking out Organizations API URLs with status code 404."""
        data = None
        self._mock_organizations_api(organization_key, data, 404)

    def mock_organizations_api_500(self, organization_key):
        """ Utility for mocking out Organizations API URLs with status code 500."""
        data = None
        self._mock_organizations_api(organization_key, data, 500)

    def _mock_organizations_api(self, organization_key, data, status_code=200):
        """ Utility for mocking out Organizations API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Organizations API calls.')

        organizations_api_url = settings.ORGANIZATIONS_API_URL
        url = '{root}/organizations/{organization_key}/'.format(
            root=organizations_api_url.strip('/'),
            organization_key=organization_key
        )
        body = json.dumps(data)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, url, body=body, content_type=CONTENT_TYPE, status=status_code)


class UserDataMixin(object):
    """ Mixin mocking User API URLs and providing fake data for testing."""
    USER_API_RESPONSE = {
        "username": "test-user",
        "name": "Test User",
        "email": "test@example.org",
    }

    def mock_user_api(self, username):
        """ Utility for mocking out User API URLs with status code 200."""
        data = self.USER_API_RESPONSE
        self._mock_user_api(username, data)

    def mock_user_api_404(self, username):
        """ Utility for mocking out User API URLs with status code 404."""
        data = None
        self._mock_user_api(username, data, 404)

    def mock_user_api_500(self, username):
        """ Utility for mocking out User API URLs with status code 500."""
        data = None
        self._mock_user_api(username, data, 500)

    def _mock_user_api(self, username, data, status_code=200):
        """ Helper method for mocking out User API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock User API calls.')

        user_api_url = settings.USER_API_URL
        url = '{root}/accounts/{username}'.format(root=user_api_url.strip('/'), username=username)
        body = json.dumps(data)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, url, body=body, content_type=CONTENT_TYPE, status=status_code)
