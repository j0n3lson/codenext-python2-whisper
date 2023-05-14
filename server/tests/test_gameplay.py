'''API test for for playing the game.'''

import os
import datetime
import json

from absl.testing import absltest
mock = absltest.mock

from http import HTTPStatus
from server import api
from server import config
from typing import Dict

TEST_USER_CONFIG = r'''
[
  {
    "id": 1,
    "username": "user01",
    "api_key": "user01apikey",
    "type": "REGULAR"
  },
  {
    "id": 2,
    "username": "user02",
    "api_key": "user02apikey",
    "type": "REGULAR"
  },
  {
    "id": 3,
    "username": "user03",
    "api_key": "user03apikey",
    "type": "REGULAR"
  }
]
''' 

class GamePlayApiTest(absltest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.addCleanup(mock.patch.stopall)

        self.mock_datetime = mock.patch.object(
            datetime, 'datetime', wraps=datetime.datetime).start()
        self.mock_datetime.now.return_value = datetime.datetime(2023, 4, 29)

        self.users = self.get_test_users(TEST_USER_CONFIG) 

        app = api.create_app(list(self.users.values()))
        app.config.update({
            "TESTING": True,
        })
        self.client = app.test_client()

    def get_test_users(self, raw_json: str) -> Dict[str, api.UserModel]:
        user_factory = api.UserModelSchema(many=True)
        users = user_factory.loads(raw_json)
        self.assertLen(users, 3)

        result = {}
        for user in users:
            result[user.username] = user
        return result

    def test_listen_when_not_enough_users_aborts(self):
        user01 = self.users['user01']
        app = api.create_app([user01])
        app.config.update({
            "TESTING": True,
        })

        response = self.client.get(f'/play/listen/user01?api_key={user01.api_key}')

        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_listen_when_currently_the_listeners_turn_sends_info_message(self):
        user01_api_key = self.users['user01'].api_key
        user02_api_key = self.users['user02'].api_key
        self.post_whisper('user01', user01_api_key, 'user02', 'first whisper')

        response = self.client.get(
            f'/play/listen/user02?api_key={user02_api_key}')

        self.assertEqual(HTTPStatus.OK, response.status_code)
        data = json.loads(response.data)
        self.assertEqual(data["info"], 'Hey user02, it\'s your turn to whisper to user03')
        self.assertEqual(data['game_status'], api.GameStatus.GAME_AWAIT_FINISH.name)
        self.assertEqual(data['current_player'], 'user02')
        self.assertEqual(data['next_player'], 'user03')
        recieved_message = json.loads(data['message'])
        self.assertEqual(recieved_message['from_user'], 'user01')
        self.assertEqual(recieved_message['message'], 'first whisper')

    def test_listen_when_not_currently_the_listeners_turn_sends_info_message(self):
        user01_api_key = self.users['user01'].api_key
        user03_api_key = self.users['user03'].api_key
        self.post_whisper('user01', user01_api_key, 'user02', 'first whisper')

        response = self.client.get(
            f'/play/listen/user03?api_key={user03_api_key}')

        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)
        data = json.loads(response.data)
        self.assertEqual(data["info"], 'Sorry, it\'s not your turn.')
        self.assertEqual(data['game_status'], api.GameStatus.GAME_AWAIT_FINISH.name)
        self.assertEqual(data['current_player'], 'user02')

    def test_whisper_when_waiting_for_game_end_sets_game_status_await_finish(self):
        user01_api_key = self.users['user01'].api_key

        whisper_response_data = self.post_whisper(
            'user01', user01_api_key, 'user02', 'first whisper')

        self.assertEqual(api.GameStatus.GAME_AWAIT_FINISH.name,
                         whisper_response_data['game_status'])

    def test_whisper_when_game_ended_sets_game_status_game_finished(self):
        user01_api_key = self.users['user01'].api_key

        whisper_response_data = self.post_whisper(
            'user01', user01_api_key, 'user02', 'first whisper')

        self.assertEqual(api.GameStatus.GAME_FINISHED.name,
                         whisper_response_data['game_status'])

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
