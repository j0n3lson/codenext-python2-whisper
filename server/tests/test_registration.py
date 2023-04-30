'''API test for registration and user management using the /users endpoint.'''

import json
import string

from absl.testing import parameterized
from http import HTTPStatus
from server.tests.base import BaseApiTestCase


class RegistrationApiTest(BaseApiTestCase, parameterized.TestCase):

    def test_always_creates_admin_user(self):
        response = self.client.get('/users/admin')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['id'], 0)
        self.assertEqual(data['user'], 'admin')
        self.assertEqual(data['type'], 'ADMIN')
        self.assertNotIn('api_key', data.keys())
        self.assertEqual(data['created_on'], '04/29/2023 00:00:00')

    def test_get_when_non_existent_user_abort_not_found(self):
        response = self.client.get('/users/not_a_user')

        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    @parameterized.named_parameters(
        ('when_empty', string.whitespace),
        ('when_has_spaces', 'user name has spaces'),
        ('when_special_characters', string.punctuation))
    def test_put_when_invalid_username_abort_bad_request(self, username):
        response = self.client.put(f'/users/{username}')

        self.assertEqual(HTTPStatus.BAD_REQUEST, response.status_code)

    def test_put_when_non_existent_user_creates_user(self):
        response = self.client.put('/users/newuser')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['user'], 'newuser')
        self.assertEqual(data['type'], 'REGULAR')
        self.assertIn('api_key', data.keys())

    def test_put_when_existing_user_abort_conflict(self):
        response = self.client.put('/users/newuser')
        self.assertEqual(HTTPStatus.OK, response.status_code)

        response = self.client.put('/users/newuser')

        self.assertEqual(HTTPStatus.CONFLICT, response.status_code)

    def test_put_when_trying_to_create_admin_user_abort_forbidden(self):
        response = self.client.put('/users/admin')

        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)
