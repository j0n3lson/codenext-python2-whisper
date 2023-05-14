# Whisper

## About

A service that lets you play Whisper Down The Lane with friends

## Stack

- Docker: Provides a container that has all the dependencies so you don't have
  to install on your local computer youself.
- VsCode: An IDE for coding. Also has container dev tools so that you can code
  inside the container.
- Flask: The API server

## Code Organization

- `/lab`: Contains code specific to the lab.
- `/server`: The flask server implementation.

## Environment Setup

### Docker

This lets us run the container that comes preinstalled with all the depedencies.
The container is configured using the `Dockerfile` in this directory which sets
up the container environment.

Head over to [Get Docker](http://docs.docker.com/get-docker/) and install it for
your system.

TIP: Internal users should use the installation instructions at
[go/install-docker](http://go/install-docker) instead.

### VSCode

VS Code is an IDE that lets us develop our code in a container. With containers,
we don't have to spend time seting up our local environment. Instead, we used
the `Dockerfile` to configure what we need in a container. When we want to code,
we just launch the container using the Remote Developer Extensions.

Check out [Developing inside a
Container](https://code.visualstudio.com/docs/devcontainers/containers) for more
details about container development.

- **Vs Code IDE:** [Download](http://code.visualstudio.com/download) and install
  VSCode for your system.
- **Remote Dev Extensions**: Install the [Remote Developer Extensions
  Pack](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)
  which contains an extension that initiates the container dev workflow when a
  `Dockerfile` is detected in a workspace.

You're all set! When you open your workspace it will suggest that you reopen the
workspace in a container.

## Running the Server

Launch your workspace in the container. Once inside, run the server like this:

    python server/main.py

You can use the REST end points using the `curl` utility:

    # Get an existing user
    curl http://localhost:5000/users/johnny

    # Create a new user. Notice the `-X PUT` option. This tells curl to send an
    # HTTP PUT request that, when, recieved tells the server to run the
    # `Users.put()` route.
    curl http://localhost:5000/users/johnny -X PUT

## Running Test

Change into the directory and run, to run all test:

    python -m unittest

## API

The service has the following APIs implemented:

## Open to all

- `/play/listen/{api_key}`: `API KEY REQUIRED`. Let's a user check for a message.
  Clients should continuously check to after they have registered.

  - `mesage: "The message"` If one is found.

  - `message: ""`, an empty message if no messages are found.

  - `message: "GAME OVER"` if the game has ended.

- `/play/whisper/{message}`: `API KEY REQUIRED`. Checks whether its the user's
  turn and sets the games current message to the given `{message}`.

## Admin only

- `/admin/snoop`: (TODO) List all messages sent by all users at the given time.
- `/admin/endgame`: (TODO) Ends the game for all players.
