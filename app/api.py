import random
import string

from enum import Enum
from datetime import datetime
from flask import Flask
from flask_restful import abort
from flask_restful import Api
from flask_restful import Resource


ADMIN_API_KEY = 'GVTu6CaxvzHQWFAn6eMi8TfVVq2BcK'

app = Flask(__name__)
api = Api(app)


class UserType(str, Enum):
    REGULAR = 1
    ADMIN = 2

    def __str__(self) -> str:
        return self.value


class User():
    '''A user in the system.'''

    def __init__(self, id, username, type, api_key):
        self.id = id
        self.username = username
        self.type = type
        self.created_on = datetime.now()
        self.api_key = api_key

    def to_json(self):
        '''Returns a JSON serializable object representing the user.'''
        return {
            'id': self.id,
            'user': self.username,
            'type': self.type,
            'created_on': self.created_on.strftime('%m/%d/%Y %H:%M:%S')
        }


# TODO(j0n3lson): Don't store the admin's API key in code. Take it as a flag
# saved in a github key.

# TODO: Move these to UserManager
api_keys = {
    'admin': ADMIN_API_KEY
}

users = {
    'admin': User(id=0, username='admin', type=UserType.ADMIN, api_key=ADMIN_API_KEY)
}


class Users(Resource):

    def get(self, username):
        '''Get the user if they exist'''
        self._abort_if_not_exists(username)
        user = users.get(username)
        return user.to_json()

    def put(self, username):
        '''Creates a new user if one doesn't already exist'''
        if username in users:
            user = users.get(username)
            created_on = user.created_on.strftime(
                '%m/%d/%Y %H:%M:%S')
            abort(409, message=f'User {username} was created on {created_on}')
        user = self._create_new_user(username)
        return user.to_json()

    def _create_new_user(self, username):
        # TODO: Move this this to UserManager
        api_key = self._generate_api_key()
        id = self._get_next_id()
        new_user = User(id=id, username=username,
                        type=UserType.REGULAR, api_key=api_key)
        users[username] = new_user
        return new_user

    def _generate_api_key(self):
        # TODO: Move this this to UserManager
        return random.choices(string.ascii_letters + string.digits, k=30)

    def _get_next_id(self):
        '''Returns the next available ID'''
        # TODO: Move this this to UserManager and track next ID when users are
        # created.
        current_users = list(users.values())
        current_users.sort(reverse=True, key=lambda user: user.id)
        return current_users[0].id + 1

    def _abort_if_not_exists(self, username):
        if username not in users:
            abort(404, message=f'User {username} does not exist')


api.add_resource(Users, '/users/<username>')

if __name__ == '__main__':
    app.run(debug=True)
