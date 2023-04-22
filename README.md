# Whisper

## About

A service that lets you play Whisper Down The Lane with friends

## Stack

- Docker: Provides a container that has all the dependencies so you don't
have to install on your local computer youself.
- VsCode: An IDE for coding. Also has container dev tools so that you can
code inside the container.
- Flask: The API server
- Cloud Run: For hosting

## Code

- `/lab`: Contains code specific to the lab.
- `/server`: The flask server implementation.

## API

The service has the following APIs implemented:

## Open to all
- `/register/user/{username}`: Registers the given `{username}`. This should be
the first thing a client calls. When called, this API registers a user and
returns a unique API key. The API key is associated with the user's ID.
- `/play/listen/{api_key}`: `API KEY REQUIRED`. Let's a user check for a message. Clients
should continuously check to after they have registered.
    - `mesage: "The message"` If one is found.
    - `message: ""`, an empty message if no messages are found. 
    - `message: "GAME OVER"` if the game has ended.
- `/play/whisper/{message}`: `API KEY REQUIRED`. Checks whether its the user's
turn and sets the games current message to the given `{message}`.

## Admin only

- `/admin/snoop`: List all messages sent by all users at the given time.
- `/admin/endgame`: Ends the game for all players.