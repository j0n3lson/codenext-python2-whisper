import random
import string

from enum import Enum
from datetime import datetime
from flask import Flask
from flask_restful import abort
from flask_restful import Api
from flask_restful import Resource


# TODO(j0n3lson): Don't store the admin's API key in code. Take it as a flag
# saved in a github key.
ADMIN_API_KEY = 'GVTu6CaxvzHQWFAn6eMi8TfVVq2BcK'

app = Flask(__name__)
api = Api(app)


class UserType(Enum):
    REGULAR = 1
    ADMIN = 2


class UserModel():
    '''A user in the system.'''
    def __init__(self, id, username, type, api_key):
        self.id = id
        self.username = username
        self.type = type
        self.created_on = datetime.now()
        self.api_key = api_key

    def to_json(self, include_api_key=False):
        '''Returns a JSON serializable object representing the user.'''
        json = {
            'id': self.id,
            'user': self.username,
            'type': self.type.name,
            'created_on': self.created_on.strftime('%m/%d/%Y %H:%M:%S')
        }
        if include_api_key:
            # TODO: Figure why a string turns into a list when we assign it to
            # the json object 
            json['api_key'] = ''.join(self.api_key)
            return json 
        return json



class UserManager():
    '''Manage users in the system'''
    def __init__(self):
        self._user_map = dict({'admin': UserModel(id=0, username='admin', type=UserType.ADMIN, api_key=ADMIN_API_KEY)})
        self._user_api_key_map = dict({'admin': ADMIN_API_KEY}) 
        self._next_id = 1

    def getUser(self, username):
        '''Returns the user or raise HTTPException if not found.'''
        user = self._user_map.get(username, None)
        if not user:
            abort(404, message=f'User {username} does not exist. Did you /users/{username}')
        return user

    def addUser(self, username):
        '''Creates new user and returns it.'''
        user = self._user_map.get(username, None)
        print(f'user: {user}')
        print(f'all_users: {self._user_map}')
        if user:
            created_on = user.created_on.strftime(
                '%m/%d/%Y %H:%M:%S')
            abort(409, message=f'User {username} was created on {created_on}')

        # Create new user
        api_key = random.choices(string.ascii_letters + string.digits, k=30)
        new_user = UserModel(id=self._next_id, username=username,
                        type=UserType.REGULAR, api_key=api_key)
        self._next_id+=1
        self._user_map[username] = new_user
        return new_user


class UsersResource(Resource):

    def __init__(self, user_manager):
        self._user_manager = user_manager

    def get(self, username):
        '''Get the user if they exist.'''
        user =  self._user_manager.getUser(username)

        # IMPORTANT: We shouldn't leak the users API key after creation.
        return user.to_json(include_api_key=False)

    def put(self, username):
        '''Creates a new user if one doesn't already exist'''
        user = self._user_manager.addUser(username)

        # IMPORTANT: It is okay to tell a user their API key once we created it.
        return user.to_json(include_api_key=True)


api.add_resource(UsersResource, '/users/<username>', resource_class_kwargs={'user_manager': UserManager()})


if __name__ == '__main__':
    app.run(debug=True)
