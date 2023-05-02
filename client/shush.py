'''Client implementation for Whisper API.'''
import json
import logging
import requests

from http import HTTPStatus
from typing import Dict

DEFAULT_API_SERVER = 'http://localhost:5000'

# Max number of times we'll retry before failing an API request.
MAX_API_ATTEMPTS = 3
DEFAULT_REQUEST_TIMEOUT_SEC = 120


class Shhh:
    '''A client that plays Whisper down the lane.'''

    def __init__(self, username: str, api_key: str):
        self._logger = self._get_logger()
        self._username = username
        self._api_key = api_key

    def _get_logger(self):
        if self._logger:
            return self._logger

        logging.basicConfig(
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%H:%M:%S',
            level=logging.DEBUG)
        return logging.getLogger('shhh_client')

    def play(self, api_server: str = DEFAULT_API_SERVER) -> None:
        '''The main game loop. Plays the game on the API server.'''
        self.listen(api_server)
        self.whisper(api_server)

    def listen(self, api_server: str) -> None:
        '''Listens until it's our turn to whisper.'''
        while True:
            params = {'api_key': self._api_key}
            url = f'{api_server}/play/listen/{self._username}'
            response = requests.put(url, params=params)

            if response.status_code == HTTPStatus.FORBIDDEN:
                self._logger.info(
                    f'Status:{HTTPStatus.FORBIDDEN.name}, game has not started')

            if response.status_code != HTTPStatus.OK:
                data = json.loads(response.json())
                self._logger.error(
                    f'Status={HTTPStatus(response.status_code).name}, data:{data}')
                continue

            data = json.loads(response.json())
            if data['current_player'] == self._username:
                whisper = json.loads[data['message']]
                from_user = whisper['from_user']
                received_message = whisper['message']
                self._logger.info(
                    f'Got message from {from_user}: {received_message}')
                self._logger.info('It\'s my turn to whisper')
                # We can break out of the loop since receiving a message implies
                # it's also our turn to whisper.
                break

    def whisper(self, api_server: str) -> None:
        '''Prompts user for details on what to whisper and then post message.'''
        while True:
            to_username = input('Who are you whispering to?: ')
            message = input('What is the message?')
            finished = input('Continue (Y/N)?')

            if finished in ['Y', 'y']:
                break

            payload = json.dumps({
                "from_username": self._username,
                "api_key": self._api_key,
                "message": message
            })

            url = f'{api_server}/play/whisper/{to_username}'
            response = self.client.post(
                url, headers={"Content-Type": "application/json"}, data=payload)

            if response.status_code == HTTPStatus.OK:
                break
