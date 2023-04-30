import random
import string
import datetime

from enum import Enum
from flask import Flask
from flask_restful import abort
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse
from http import HTTPStatus
from typing import Dict, Tuple, Type


# The JSON object sent to clients.
UserMessageApiResponse = Dict[str, str]
UserModelApiResponse = Dict[str, str]
WhisperPutApiResponse = Dict[str, str]


# TODO(j0n3lson): Don't store the admin's API key in code. Take it as a flag
# saved in a github key.
ADMIN_API_KEY = 'GVTu6CaxvzHQWFAn6eMi8TfVVq2BcK'
ADMIN_USERNAME = 'admin'


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

    def __init__(self, id: int, username: str, type: UserType, api_key: str):
        self.id = id
        self.username = username
        self.type = type
        self.created_on = datetime.datetime.now()
        self.api_key = api_key

    def to_json(self, include_api_key=False) -> UserModelApiResponse:
        '''Returns a JSON serializable object representing the user.'''
        # TODO: Use flask.jsonify here: https://www.fullstackpython.com/flask-json-jsonify-examples.html
        json = {
            'id': self.id,
            'user': self.username,
            'type': self.type.name,
            'created_on': self.created_on.strftime('%m/%d/%Y %H:%M:%S')
        }
        if include_api_key:
            json['api_key'] = self.api_key
            return json
        return json


class UserManager():
    '''Manage users in the system'''

    def __init__(self):
        # A map of username to UserModel object.
        self._user_map: Dict[str, UserModel] = dict()

        # A map of api key to UserModel object.
        self._user_api_key_map: Dict[str, UserModel] = dict()

        # A map of user ID to UserModel Object.
        self._user_id_map: Dict[int, UserModel] = dict()

        self._next_id = 0
        self.add_user(ADMIN_USERNAME, user_type=UserType.ADMIN,
                     api_key=ADMIN_API_KEY)

    def get_user_by_name(self, username: str) -> UserModel:
        '''Returns the user or raise HTTPException if not found.'''
        user = self._user_map.get(username, None)
        if not user:
            abort(
                HTTPStatus.NOT_FOUND, message=f'User {username} does not exist. Did you /users/{username}')
        return user

    def get_user_by_id(self, id: int) -> UserModel:
        '''Returns the user with given id or raise.'''
        user = self._user_id_map.get(id, None)
        if not user:
            abort(
                HTTPStatus.NOT_FOUND, message=f'No user with id={id} found. Did you /users/<username>')
        return user

    def add_user(self, username: str, user_type: UserType = UserType.REGULAR, api_key: str = None) -> UserModel:
        '''Creates new user and returns it.'''
        user = self._user_map.get(username, None)
        if user:
            created_on = user.created_on.strftime(
                '%m/%d/%Y %H:%M:%S')
            abort(HTTPStatus.CONFLICT,
                  message=f'User {username} was created on {created_on}')

        # Create new user
        if not api_key:
            api_key = ''.join(random.choices(
                string.ascii_letters + string.digits, k=30))
        new_user = UserModel(id=self._next_id, username=username,
                             type=user_type, api_key=api_key)
        self._next_id += 1
        self._user_map[username] = new_user
        self._user_api_key_map[new_user.api_key] = new_user
        self._user_id_map[new_user.id] = new_user
        return new_user

    def get_users_count(self) -> int:
        return len(self._user_map)

    def is_authorized_or_abort(self, username, api_key) -> None:
        '''Check that username exist and is associated with the given key.'''
        # Expect this to throw if user doesn't exist.
        user = self.get_user_by_name(username)
        if user.api_key != api_key:
            abort(
                HTTPStatus.FORBIDDEN, f'Specified API key ({api_key}) does not match for {username}.')


class GameManager():
    '''Manages the game.'''

    def __init__(self, user_manager: UserManager):
        self._game_status = GameStatus.GAME_NOT_STARTED

        self._user_manager = user_manager
        self._current_player_id = 1
        self._next_player_id = 2
        self._messages: Dict[str, UserMessageApiResponse]

    def get_game_status(self) -> GameStatus:
        '''Get the current game status.'''
        return self._game_status

    def set_game_status(self, status: GameStatus) -> None:
        self._game_status = status

    def get_current_player_id(self) -> int:
        '''Get the id of the user who should whisper now.'''
        return self._current_player_id

    def set_current_player_id(self, id: int) -> None:
        self._current_player_id = id

    def get_current_player(self) -> UserModel:
        '''Like getCurrentPlayer() but returns the whole user object.'''
        return self._user_manager.get_user_by_id(self._current_player_id)

    def set_next_player_id(self, id: int) -> None:
        self._current_player_id = id

    def get_next_player_id(self) -> int:
        '''Get the id of the user who should whisper next.'''
        return self._next_player_id

    def get_next_player(self) -> UserModel:
        '''Like getNextPlayerId() but returns the whole user object.'''
        return self._user_manager.get_user_by_id(self._next_player_id)

    def get_player_count(self) -> int:
        return self._user_manager.get_users_count()

    def get_player_by_name(self, username: str) -> UserModel:
        return self._user_manager.get_user_by_name(username)

    def get_message_for_user(self, username: str) -> UserMessageApiResponse:
        if username not in self._messages:
            abort(HTTPStatus.NOT_FOUND, f'No messages for {username}')
        return self._messages[username]

    def set_message_for_user(self, from_username: str, to_username: str, message: str):
        if to_username in self._messages:
            abort(HTTPStatus.FORBIDDEN,
                  f'User {to_username} has already gotten a message.')
        self._messages[to_username] = {
            'from_user': from_username,
            'message': message
        }

    def is_authorized_or_abort(self, username: str, api_key: str):
        '''Check if user is allowed or raise HTTPException'''
        # Expect this to raise for invalid user.
        self._user_manager.is_authorized_or_abort(username, api_key)


class Users(Resource):
    '''Handles the /users endpoint'''

    def __init__(self, user_manager: UserManager):
        self._user_manager = user_manager

    def get(self, username) -> UserModelApiResponse:
        '''Get the user if they exist.'''
        user = self._user_manager.get_user_by_name(username)

        # IMPORTANT: We shouldn't leak the users API key after creation.
        return user.to_json(include_api_key=False)

    def put(self, username: str) -> UserModelApiResponse:
        '''Creates a new user if one doesn't already exist'''
        # Defensive: They should never be able to create an 'admin' user
        if username == ADMIN_USERNAME:
            abort(HTTPStatus.FORBIDDEN,
                  message=f'You cannot register the \"{ADMIN_USERNAME}\" username')

        user = self._user_manager.add_user(username)

        # IMPORTANT: It is okay to tell a user their API key once we created it.
        return user.to_json(include_api_key=True)


class Whisper(Resource):
    '''Handles the /play/whisper endpoint.'''

    def __init__(self, game_manager: GameManager):
        self._game_manager = game_manager

    def put(self, username: str) -> WhisperPutApiResponse:
        '''Send a message to a given user'''
        params = self._get_request_params()
        api_key = params['api_key']
        from_username = username
        to_username = params['to_username']
        message = params['message']

        # Validate User
        self._game_manager.is_authorized_or_abort(from_username, api_key)

        # Check if it's okay to play right now.
        self._can_whisper_or_abort()

        # Get the next two players to go.
        from_user, to_user = self._get_players_or_abort(
            from_username, to_username)

        # If we got here, the user is authorized and can whisper to the
        # recipient so we can start the game.
        if self._game_manager.get_game_status() == GameStatus.GAME_NOT_STARTED:
            # TODO: Block registration when game is started.
            self._game_manager.set_game_status(GameStatus.GAME_STARTED)

        # Whisper: Add a Whisper {message, from_user, to_user} to the model
        self._game_manager.set_message_for_user(
            from_user.username, to_user.username, message)
        self._game_manager.set_current_player_id(to_user.id)
        self._game_manager.set_next_player_id(to_user.id + 1)

        # Check if we're ending or should wait for the end of the game.
        player_count = self._game_manager.get_player_count()
        if to_user.id == player_count - 2:
            # The next pair is the last pair
            self._game_manager.set_game_status(GameStatus.GAME_AWAIT_FINISH)
        elif to_user.id == player_count - 1:
            # We're on the last pair, the game is over
            self._game_manager.set_game_status(GameStatus.GAME_FINISHED)

        return {
            'info': f'Sent messsage to {to_user.username}',
            'game_status': self._game_manager.get_game_status().name
        }

    def _can_whisper_or_abort(self) -> None:
        '''Check if we should start or abort'''
        # Are we in the right state?
        current_state = self._game_manager.get_game_status()
        if current_state == GameStatus.GAME_FINISHED:
            abort(
                HTTPStatus.FORBIDDEN, f'State: {current_state}. Game has finished. You should start listening for the next game to start.')

        # Are there enough players?
        player_count = self._game_manager.get_player_count()
        if player_count < 3:
            abort(
                HTTPStatus.FORBIDDEN, f'There are not enough players. Need 3, have {player_count} players registered.')

    def _get_players_or_abort(self, from_username, to_username) -> Tuple[UserModel]:
        '''Checks that the user can whisper to the other user or aborts.'''
        from_user = self._game_manager.get_player_by_name(from_username)
        if from_user.id != self._game_manager.get_current_player_id():
            abort(HTTPStatus.FORBIDDEN,
                  f'Sorry, {from_username}, it is not your turn!')

        to_user = self._game_manager.get_player_by_name(to_username)
        if to_user.id != self._game_manager.get_next_player_id():
            abort(HTTPStatus.FORBIDDEN, f'Sorry, {to_username} is not next!')

        return from_user, to_user

    def _get_request_params(self) -> Type[reqparse.Namespace]:
        # TODO: Not sure if this return pytype annotation is correct.
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

    def __init__(self, game_manager: GameManager):
        self._game_manager = game_manager

    def get(self, username: str) -> UserMessageApiResponse:
        '''Listens for whispers sent to the user

        The response indicates the username of the current whisperer and the
        next whisperer. If the given user is the current whisper, then the
        response indicates that they should go via the game status.
        '''
        api_key = self._get_request_params().get('api_key')
        self._game_manager.is_authorized_or_abort(username, api_key)

        game_status = self._game_manager.get_game_status()
        current_player = self._game_manager.get_current_player()
        next_player = self._game_manager.get_next_player()

        if game_status == GameStatus.GAME_NOT_STARTED:
            abort(HTTPStatus.TOO_EARLY,
                  f'Too early. The game has not started yet.')
        if game_status == GameStatus.GAME_AWAIT_FINISH:
            # It's not their turn but we're waiting for someone else to go.
            abort(
                HTTPStatus.OK, f'Everyone has gone except the last pair. Waiting for {current_player.username} to whisper to {next_player.username}.')

        if current_player.username == username:
            # It's the user's turn, they should take it.
            return {
                'info': f'Hey {username}, it\'s your turn to whisper to {next_player}',
                'game_status': game_status.name,
                'current_whisperer': username,
                'next_whisperer': next_player,
            }
        return self._game_manager.get_message_for_user(username)

    def _get_request_params(self) -> Type[reqparse.Namespace]:
        # TODO: Not sure if this return pytype annotation is correct.
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str,
                            help='The api key for the user')
        return parser.parse_args(strict=True)


def create_app():
    # Game depdendencies

    user_manager = UserManager()
    game_manager = GameManager(user_manager)

    # Init app
    app = Flask(__name__)
    api = Api(app)

    # Setup routes
    api.add_resource(Users, '/users/<username>',
                     resource_class_kwargs={'user_manager': UserManager()})
    api.add_resource(Listen, '/play/listen/<username>',
                     resource_class_kwargs={'game_manager': game_manager})
    api.add_resource(Whisper, '/play/whisper/<username>',
                     resource_class_kwargs={'game_manager': game_manager})
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
