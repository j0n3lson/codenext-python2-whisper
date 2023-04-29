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
    GAME_NOT_STARTED = 1
    GAME_STARTED = 2
    GAME_AWAIT_FINISH = 3
    GAME_FINISHED = 3


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

    def toJson(self, include_api_key=False):
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

        self._next_id = 1
        self.addUser('admin', api_key=ADMIN_API_KEY)

    def getUserByName(self, username):
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

    def getUsersCount(self):
        return len(self._user_map)

    def isAuthorizedOrAbort(self, username, api_key):
        '''Check that username exist and is associated with the given key.'''
        # Expect this to throw if user doesn't exist.
        user = self.getUserByName(username)
        if user.api_key != api_key:
            abort(
                403, f'Specified API key ({api_key}) does not match for {username}.')


class GameManager():
    '''Manages the game.'''

    def __init__(self, user_manager):
        self._game_status = GameStatus.GAME_NOT_STARTED

        self._user_manager = user_manager
        # Note: These get updated once the game starts.
        self._current_player_id = 1
        self._next_player_id = 2

    def getGameStatus(self):
        '''Get the current game status.'''
        return self._game_status

    def setGameStatus(self, status):
        self._game_status = status

    def getCurrentPlayerId(self):
        '''Get the id of the user who should whisper now.'''
        return self._current_player_id

    def getCurrentPlayer(self):
        '''Like getCurrentPlayer() but returns the whole user object.'''
        return self._user_manager.getUserById(self._current_player_id)

    def setNextPlayerId(self, id):
        self._current_player_id = id

    def getNextPlayerId(self):
        '''Get the id of the user who should whisper next.'''
        return self._next_player_id

    def getNextPlayer(self):
        '''Like getNextPlayerId() but returns the whole user object.'''
        return self._user_manager.getUserById(self._next_player_id)

    def setNextPlayerId(self, id):
        self._next_player_id = id

    def getPlayerCount(self):
        return self._user_manager.getUsersCount()

    def getPlayerByName(self, username):
        return self._user_manager.getUserByName(username)

    def getMessageForUser(self, username):
        if username not in self._messages:
            abort(404, f'No messages for {username}')
        return self._messages[username]

    def setMessageForUser(self, from_username, to_username, message):
        if to_username in self._messages:
            abort(403, f'User {to_username} has already gotten a message.')
        self._messages[to_username] = {
            'from_user': from_username,
            'message': message
            }

    def isAuthorizedOrAbort(self, username, api_key):
        '''Check if user is allowed or raise HTTPException'''
        # Expect this to raise for invalid user.
        self._user_manager.isAuthorizedOrAbort(username, api_key)


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
        return user.toJson(include_api_key=True)


class Whisper(Resource):
    '''Handles the /play/whisper endpoint.'''

    def __init__(self, game_manager):
        self._game_manager = game_manager

    def put(self, username):
        '''Send a message to a given user'''
        params = self._getRequestParams()
        api_key = params['api_key']
        from_username = username
        to_username = params['to_username']
        message = params['message']

        # Validate User
        self._game_manager.isAuthorizedOrAbort(from_username, api_key)

        # Check if it's okay to play right now.
        self._canWhisperOrAbort(from_username)

        # Get the next two players to go.
        from_user, to_user = self._getPlayersOrAbort(
            from_username, to_username)

        # If we got here, the user is authorized and can whisper to the
        # recipient so we can start the game.
        if self._game_manager.getGameStatus() == GameStatus.GAME_NOT_STARTED:
            # TODO: Block registration when game is started.
            self._game_manager.setGameStatus(GameStatus.GAME_STARTED)

        # Whisper: Add a Whisper {message, from_user, to_user} to the model
        self._game_manager.setMessageForUser(from_user.username, to_user.username, message)
        self._game_manager.setCurrentPlayerId(to_user.id)
        self._game_manager.setNextPlayerId(to_user.id + 1)

        # Check if we're ending or should wait for the end of the game.
        player_count = self._game_manager.getPlayerCount()
        if to_user.id == player_count - 2:
            # The next pair is the last pair
            self._game_manager.setGameStatus(GameStatus.GAME_AWAIT_FINISH)
        elif to_user.id == player_count - 1:
            # We're on the last pair, the game is over
            self._game_manager.setGameStatus(GameStatus.GAME_FINISHED)

        return {
            'info': f'Sent messsage to {to_user.username}',
            'game_status': self._game_manager.getGameStatus().name
        }

    def _canWhisperOrAbort(self, from_username):
        '''Check if we should start or abort'''
        # Are we in the right state?
        current_state = self._game_manager.getGameStatus()
        if current_state == GameStatus.GAME_FINISHED:
            abort(
                403, f'State: {current_state}. Game has finished. You should start listening for the next game to start.')

        # Are there enough players?
        player_count = self._game_manager.getPlayerCount()
        if player_count < 3:
            abort(
                403, f'There are not enough players. Need 3, have {player_count} players registered.')

    def _getPlayersOrAbort(self, from_username, to_username):
        '''Checks that the user can whisper to the other user or aborts.'''
        from_user = self._game_manager.getPlayerByName(from_username)
        if from_user.id != self._game_manager.getCurrentPlayerId():
            abort(403, f'Sorry, {from_username}, it is not your turn!')

        to_user = self._game_manager.getPlayerByName(to_username)
        if to_user.id != self._game_manager.getNextPlayerId():
            abort(403, f'Sorry, {to_username} is not next!')

        return from_user, to_user

    def _getRequestParams(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str,
                            help='The api key for the user')

        parser.add_argument('to_username', type=str,
                            help='The user that will get a message.')
        parser.add_argument('message', type=str,
                            help='The message that will be sent.')
        return parser.parse_args(strict=True)


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
        self._game_manager.isAuthorizedOrAbort(username, api_key)

        game_status = self._game_manager.getGameStatus()
        current_player = self._game_manager.getCurrentPlayer()
        next_player = self._game_manager.getNextPlayer()

        if game_status == GameStatus.GAME_NOT_STARTED:
            abort(425, f'Too early. The game has not started yet.')
        if game_status == GameStatus.GAME_AWAIT_FINISH:
            # It's not their turn but we're waiting for someone else to go.
            abort(
                200, f'Everyone has gone except the last pair. Waiting for {current_player.username} to whisper to {next_player.username}.')

        if current_player.username == username:
            # It's the user's turn, they should take it.
            return {
                'info': f'Hey {username}, it\'s your turn to whisper to {next_player}',
                'game_status': game_status.name,
                'current_whisperer': username,
                'next_whisperer': next_player,
            }
        return self._game_manager.getMessageForUser(username)

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
