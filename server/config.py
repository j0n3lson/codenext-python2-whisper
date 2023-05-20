'''Read in config.'''

from marshmallow.exceptions import ValidationError
from typing import List

import api


class InvalidConfigError(Exception):
    '''When configuration is invalid.'''


def read_user_config(file_path: str) -> List[api.UserModel]:
    '''Reads the list of users from a file.

    Args:
        file_path: The path a file containing users
    Returns:
        A dict whose key is the username and whose value is the api key for that
        user.
    '''
    json_data = None
    with open(file_path, 'r') as config_file:
        json_data = config_file.read()

    schema = api.UserModelSchema(many=True)
    try:
        users = schema.loads(json_data)
    except ValidationError as e:
        raise InvalidConfigError(e)

    if len(users) < 2:
        raise InvalidConfigError('Not enough players to play. Minimum is two.')

    for user in users:
        if user.type == api.UserType.ADMIN:
            raise InvalidConfigError(
                f'Found user {user.username} with type=ADMIN. Admin users are not allowed in the config.')

    return users
