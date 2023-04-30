'''API test for for playing the game.'''

import json

from http import HTTPStatus
from server.tests.base import BaseApiTestCase
from server import api


class GamePlayApiTest(BaseApiTestCase):

    def test_listen_when_not_enough_users_aborts(self):
        api_key = self.register_user('user01')

        response = self.client.get(f'/play/listen/user01?api_key={api_key}')

        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_listen_when_waiting_for_user_to_take_turn_returns_info_message(self):
        user01_api_key = self.register_user('user01')
        user02_api_key = self.register_user('user02')
        self.register_user('user03')
        self.post_whisper('user01', user01_api_key, 'user02', 'first whisper')

        response = self.client.get(
            f'/play/listen/user02?api_key={user02_api_key}')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.data)
        self.assertEqual(data["info"], 'Hey user02, it\'s your turn to whisper to user03')
        self.assertEqual(data['game_status'], api.GameStatus.GAME_AWAIT_FINISH.name)
        self.assertEqual(data['next_player'], 'user03')
        response_whisper = json.loads(data['message'])
        self.assertEqual(response_whisper['from_user'], 'user01')
        self.assertEqual(response_whisper['message'], 'first whisper')

    def test_whisper_when_waiting_for_game_end_sets_game_status_await_finish(self):
        user01_api_key = self.register_user('user01')
        self.register_user('user02')
        self.register_user('user03')
        whisper_response_data = self.post_whisper(
            'user01', user01_api_key, 'user02', 'first whisper')
        self.assertEqual(api.GameStatus.GAME_AWAIT_FINISH.name,
                         whisper_response_data['game_status'])

    def register_user(self, username: str) -> str:
        '''Registers user and returns the generated API key.'''
        response = self.client.put(f'/users/{username}')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.get_data(as_text=True))
        return data['api_key']

    def post_whisper(self, from_username: str, api_key: str, to_username: str, message: str):
        '''Post a message from a user to another and return the response data.'''
        payload = json.dumps({
            "from_username": from_username,
            "api_key": api_key,
            "message": message
        })
        response = self.client.post(
            f'/play/whisper/{to_username}', headers={"Content-Type": "application/json"}, data=payload)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.data)
        return data
