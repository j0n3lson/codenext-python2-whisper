import random
import string

from enum import Enum
from datetime import datetime
from flask import Flask
from flask import request
from flask_restful import abort
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse


# TODO(j0n3lson): Don't store the admin's API key in code. Take it as a flag
# saved in a github key.
ADMIN_API_KEY = 'GVTu6CaxvzHQWFAn6eMi8TfVVq2BcK'

app = Flask(__name__)
api = Api(app)


class GameStatus(Enum):
    NOT_STARTED = 1
    GAME_STARTED = 2
    WAITING_FOR_END = 3
    GAME_OVER = 3


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
        # A map of username to UserModel object.
        self._user_map = dict()

        # A map of api key to UserModel object.
        self._user_api_key_map = dict()

        # A map of user ID to UserModel Object.
        self._user_id_map = dict()

        self._next_id = 0
        self.addUser('admin', api_key=ADMIN_API_KEY)

    def getUser(self, username):
        '''Returns the user or raise HTTPException if not found.'''
        user = self._user_map.get(username, None)
        if not user:
            abort(
                404, message=f'User {username} does not exist. Did you /users/{username}')
        return user

    def getUserById(self, id):
        '''Returns the user with given id or raise.'''
        user = self._user_id_map.get(id, None)
        if not user:
            abort(
                404, message=f'No user with id={id} found. Did you /users/<username>')
        return user

    def addUser(self, username, api_key=None):
        '''Creates new user and returns it.'''
        user = self._user_map.get(username, None)
        if user:
            created_on = user.created_on.strftime(
                '%m/%d/%Y %H:%M:%S')
            abort(409, message=f'User {username} was created on {created_on}')

        # Create new user
        if not api_key:
            api_key = random.choices(
                string.ascii_letters + string.digits, k=30)
        new_user = UserModel(id=self._next_id, username=username,
                             type=UserType.REGULAR, api_key=api_key)
        self._next_id += 1
        self._user_map[username] = new_user
        self._user_api_key_map[new_user.api_key] = new_user
        self._user_id_map[new_user.id] = new_user
        return new_user

    def checkUserIsAllowedOrRaise(self, username, api_key):
        '''Check that username exist and is associated with the given key.'''
        # Expect this to throw if user doesn't exist.
        user = self.getUser(username)
        if user.api_key != api_key:
            abort(
                403, f'Specified API key ({api_key}) does not match for {username}.')


class GameManager():
    '''Manages the game.'''

    def __init__(self, user_manager):
        self._game_status = GameStatus.NOT_STARTED

        self._user_manager = user_manager
        # Note: These get updated once the game starts.
        self._current_whisperer = None
        self._next_whisperer = None

    # TODO: Move to WhisperEndpoint.post()
    def whisper(self, username, api_key):
        self.checkUserIsAllowedOrRaise(username, api_key)
        user = self._user_manager.getUser(username)

        if self._game_status == GameStatus.NOT_STARTED:
            if user.id != 1:
                # We're begining the game, the user should be the user with the
                # lowest ID.
                expected_whisperer = self._user_manager.getUserById(id=1)
                abort(
                    403, 'Game is starting, expecting whisperer to be {expected_whisperer.username}')
            if user.id == 1:
                self._game_status = GameStatus.GAME_STARTED
                # TODO: Record the message

    def getGameStatus(self):
        '''Get the current game status.'''
        return self._game_status

    def getCurrentWhisperer(self):
        '''Get the user who should whisper.'''
        return self._current_whisperer

    def getNextWhisperer(self):
        '''Get the user who should shiper next.'''
        return self._next_whisperer

    # TODO: Move to WhisperEndpoint
    def checkUserIsAllowedOrRaise(self, username, api_key):
        '''Check if user is allowed or raise HTTPException'''
        # Expect this to raise for invalid user.
        self._user_manager.checkUserIsAllowedOrRaise(username, api_key)


class Users(Resource):
    '''Handles the /users/ endpoint'''

    def __init__(self, user_manager):
        self._user_manager = user_manager

    def get(self, username):
        '''Get the user if they exist.'''
        user = self._user_manager.getUser(username)

        # IMPORTANT: We shouldn't leak the users API key after creation.
        return user.to_json(include_api_key=False)

    def put(self, username):
        '''Creates a new user if one doesn't already exist'''
        user = self._user_manager.addUser(username)

        # IMPORTANT: It is okay to tell a user their API key once we created it.
        return user.to_json(include_api_key=True)


class Whisper(Resource):
    '''Handles the /play/whisper endpoint.'''

    def __init__(self, game_manager):
        self._game_manager = game_manager

    def put(self, username):
        '''Send a message to a given user'''
        params = self._getRequestParams()
        api_key = params['api_key']
        from_user = username
        to_user = params['to_user']
        message = params['message']

        # Validate User
        self._game_manager.checkUserIsAllowedOrRaise(from_user, api_key)

        # Check if we're in the right state
        #   - Is the game in GAME_AWAIT_FINISH, GAME_FINISHED?
        current_state = self._game_manager.getGameStatus()
        if current_state == GameState.GAME_FINISHED:
            abort(
                403, f'State: {current_state}. Game has finished. You should start listening for the next game to start.')
        elif current_state == GameState.GAME_AWAIT_FINISH:
            abort(
                403, f'State: {current_state}. You cannot whisper now, we are waiting for the last whisper.')

        #   - Are there a minimum number of registered users?
        elif current_state in [GameState.GAME_STARTED, GameState.GAME_AWAIT_START]:
            # If this is the first Whisperer, then we should move to GAME_STARTED.
            if self._game_manager.getCurrentWhisperer() == None:
                self._game_manager.setGameState(GameState.GAME_AWAIT_START)

        # Whisper: Add a Whisper {message, from_user, to_user} to the model

        # Reply

    def _getRequestParams(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str,
                            help='The api key for the user')
        return parser.parse_args(strict=True)

        pass


class Listen(Resource):
    '''Handles the /play/listen endpoint'''

    def __init__(self, game_manager):
        self._game_manager = game_manager

    def get(self, username):
        '''Listens for whispers sent to the user

        The response indicates the username of the current whisperer and the
        next whisperer. If the given user is the current whisper, then the
        response indicates that they should go via the game status.
        '''
        api_key = self._getRequestParams().get('api_key')
        self._game_manager.checkUserIsAllowedOrRaise(username, api_key)

        game_status = self._game_manager.getGameStatus()
        current_whisperer = self._game_manager.getCurrentWhisperer()
        next_whisperer = self._game_manager.getNextWhisperer()

        if game_status == GameStatus.GAME_OVER:
            # The game already ended.
            abort(410, f'Too late, the game has already ended.')
        elif game_status == GameStatus.NOT_STARTED:
            # The first person hasn't gone.
            abort(425, f'Too early. The game has not started yet.')
        elif game_status == GameStatus.WAITING_FOR_END:
            # It's not their turn but we're waiting for someone else to go.
            abort(
                200, f'Everyone has gone except the last pair. Waiting for {current_whisperer} to whisper to {next_whisperer}.')

        if current_whisperer.username == username:
            # It's the user's turn, they should take it.
            return {
                'message': f'Hey {username}, it\'s your turn to whisper to {next_whisperer}',
                'current_whisper': username,
                'next_whisper': next_whisperer,
                'game_status': game_status.name
            }

    def _getRequestParams(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str,
                            help='The api key for the user')
        return parser.parse_args(strict=True)


# Game depdendencies

user_manager = UserManager()
game_manager = GameManager(user_manager)

# Setup routes
api.add_resource(Users, '/users/<username>',
                 resource_class_kwargs={'user_manager': UserManager()})
api.add_resource(Listen, '/play/listen/<username>',
                 resource_class_kwargs={'game_manager': game_manager})
api.add_resource(Whisper, '/play/whisper/<username>',
                 resource_class_kwargs={'game_manager': game_manager})


if __name__ == '__main__':
    app.run(debug=True)
