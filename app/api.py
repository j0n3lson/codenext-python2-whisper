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


# TODO(j0n3lson): Don't store the admin's API key in code. Take it as a flag
# saved in a github key.
api_keys = {
    'admin': ADMIN_API_KEY
}

users = {
    'admin': User(id=0, username='admin', type=UserType.ADMIN, api_key=ADMIN_API_KEY)
}


class Users(Resource):
    def _abort_if_not_exists(self, username):
        if username not in users:
            abort(404, message=f'User {username} does not exist')

    def get(self, username):
        self._abort_if_not_exists(username)
        user = users.get(username)
        return {
            'id': user.id,
            'user': user.username,
            'type': user.type,
            'created_on': user.created_on.strftime('%m/%d/%Y %H:%M:%S')
        }


api.add_resource(Users, '/users/<username>')

if __name__ == '__main__':
    app.run(debug=True)
