'''Unit test for the /users endpoint.'''

import json

from http import HTTPStatus
from server.tests.base import BaseTestCase



class UsersTest(BaseTestCase):

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

    def test_put_when_non_existent_user_creates_user(self):
        response = self.client.put('/users/newuser')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['user'], 'newuser')
        self.assertEqual(data['type'], 'REGULAR')
        self.assertIn('api_key', data.keys())

    def test_put_when_existing_user_does_not_create_user(self):
        response = self.client.put('/users/newuser')
        self.assertEqual(HTTPStatus.OK, response.status_code)

        response = self.client.put('/users/newuser')

        self.assertEqual(HTTPStatus.CONFLICT, response.status_code)

    def test_put_when_trying_to_create_admin_user_abort_forbidden(self):
        response = self.client.put('/users/admin')

        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)
