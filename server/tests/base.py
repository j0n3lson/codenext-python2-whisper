'''Base case for all tests.'''

import datetime

from server import api
from absl.testing import absltest

mock = absltest.mock


class BaseTestCase(absltest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.addCleanup(mock.patch.stopall)

        self.mock_datetime = mock.patch.object(
            datetime, 'datetime', wraps=datetime.datetime).start()
        self.mock_datetime.now.return_value = datetime.datetime(2023, 4, 29)

        app = api.createApp()
        app.config.update({
            "TESTING": True,
        })
        self.client = app.test_client()

    def tearDown(self) -> None:
        super().tearDown()
