from nba_ws import app
from nba_ws.models import SearchField
import unittest


class TestSearchAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()


if __name__ == "__main__":
    unittest.main(verbosity=2)
