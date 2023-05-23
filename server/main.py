
from absl import app
from absl import flags
import logging
import os

import api
import config

FLAGS = flags.FLAGS

_DEFAULT_USER_CONFIG = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'user_config.json')

flags.DEFINE_string('user_config_path', _DEFAULT_USER_CONFIG,
                    ('Path to a file that contains users and their API key. The '
                     'file should contain one user/key per line separated by a '
                     'single space.'))


def get_logger() -> logging.Logger:
    '''Returns a configured logger instance'''
    logging.basicConfig(
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)
    return logging.getLogger("whisper_server")


def main(argv):
    users = config.read_user_config(FLAGS.user_config_path)
    logger = get_logger()
    logger.info(
        f'Loaded {len(users)} users from config \'{FLAGS.user_config_path}\'')

    admin_user = api.UserModel(id=0, username=api.ADMIN_USERNAME,
                               type=api.UserType.ADMIN, api_key=api.ADMIN_API_KEY)
    users.append(admin_user)

    flask_app = api.create_app(users)
    flask_app.run(debug=True)


if __name__ == '__main__':
    app.run(main)
