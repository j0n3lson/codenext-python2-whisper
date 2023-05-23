'''Test start up methods for server.'''

import json

from absl.testing import absltest
from absl.testing import parameterized
from six import PY2
from typing import Union

from .context import server
from server import api
from server import config


mock = absltest.mock


class UserConfigTest(parameterized.TestCase):
    '''Test parsing user config.'''

    def test_when_config_user_is_acceptable_retuns_expected_user(self):
        user1 = make_test_user(1, 'user1', 'abc', 'REGULAR')
        user2 = make_test_user(2, 'user2', 'def', 'REGULAR')
        json_data = json.dumps([user1, user2])
        self.setup_mock_open(json_data)

        result = config.read_user_config('unused_file_path')

        schema = api.UserModelSchema(many=True)
        result_json = schema.dump(result)
        expected_json = schema.dump([
            api.UserModel(1, 'user1', api.UserType.REGULAR, 'abc'),
            api.UserModel(2, 'user2', api.UserType.REGULAR, 'def')
        ])
        self.assertEqual(result_json, expected_json)

    @parameterized.named_parameters(
        ('when_missing_id', None, '', 'abc', 'REGULAR'),
        ('when_missing_username', 1, '', 'abc', 'REGULAR'),
        ('when_invalid_username', 1, 'BadUserName', 'abc', 'REGULAR'),
        ('when_missing_api_key', 1, 'user01', '', 'REGULAR'),
        ('when_invalid_api_key', 1, 'user01', '####', 'REGULAR'),
        ('when_missing_user_type', 1, 'user01', 'abc', ''),
        ('when_invalid_user_type', 1, 'user01', 'abc', 'regular'),
        ('when_reserved_id', 0, 'user01', 'abc', 'REGULAR'),
        ('when_reserved_user_type', 1, 'user01', 'abc', 'ADMIN'),
        ('when_reserved_username', 1, 'admin', 'abc', 'ADMIN'),
    )
    def test_when_config_is_invalid_raises_raises(self, id: Union[str, None], username: str, api_key: str, user_type: str):
        user1 = make_test_user(id, username, api_key, user_type)
        user2 = make_test_user(id, username, api_key, user_type)
        json_data = json.dumps([user1, user2])
        self.setup_mock_open(json_data)

        self.assertRaises(config.InvalidConfigError,
                          config.read_user_config, file_path='unused_file_path')

    def test_when_config_has_too_few_users_raises(self):
        user1 = make_test_user(0, 'foo_user', 'abc', 'REGULAR')
        json_data = json.dumps([user1])
        self.setup_mock_open(json_data)

        self.assertRaises(config.InvalidConfigError,
                          config.read_user_config, file_path='unused_file_path')

    def setup_mock_open(self, data):
        '''Setup mock open() with the given data and return the created mock.'''
        target = '__builtin__.open' if PY2 else 'builtins.open'
        return mock.patch(target, mock.mock_open(read_data=data)).start()


def make_test_user(id: Union[str, None], username: str, api_key: str, user_type: str):
    data = {}
    if id != None:
        data['id'] = id
    if username:
        data['username'] = username
    if api_key:
        data['api_key'] = api_key
    if user_type:
        data['type'] = user_type
    return data

if __name__ == '__main__':
    absltest.main()