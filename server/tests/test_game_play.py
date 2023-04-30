'''API test for for playing the game.'''

import json

from http import HTTPStatus
from server.tests.base import BaseApiTestCase


class GamePlayApiTest(BaseApiTestCase):

    def test_listen_when_not_enough_users_aborts(self):
        api_key = self.register_user('user01')

        response = self.client.get(f'/play/listen/user01?api_key={api_key}')

        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def register_user(self, username: str) -> str:
        '''Registers user and returns the generated API key.'''
        response = self.client.put(f'/users/{username}')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.get_data(as_text=True))
        return data['api_key']
