'''Read in config.'''

from server import api
from typing import List
from marshmallow.exceptions import ValidationError

class InvalidConfigError(Exception):
    '''When configuration is invalid.'''
    pass


def read_user_config(file_path: str) -> List[api.UserModel]:
    '''Reads the list of users from a file.

    Args:
        file_path: The path a file containing users
    Returns:
        A dict whose key is the username and whose value is the api key for that
        user.
    '''
    # Note: Set many=True since the config is a list.
    json_data = None
    with open(file_path, 'r') as config_file:
        json_data = config_file.read()

    print(f'##DEBUG: json_data={json_data}')
    schema = api.UserModelSchema(many=True)
    try:
        users = schema.loads(json_data)
    except ValidationError as e:
        raise InvalidConfigError(e)

    print(f'##DEBUG: len(users)={len(users)}')
    if len(users) < 2:
        raise InvalidConfigError('Not enough players to play. Minimum is two.')

    for user in users:
        if user.type == api.UserType.ADMIN:
            raise InvalidConfigError(
                f'Found user {user.username} with type=ADMIN. Admin users are not allowed in the config.')

    return users
