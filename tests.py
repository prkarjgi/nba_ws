from nba_ws import create_app, db
from config import TestingConfig
import unittest
import json

BASE_URL = "http://127.0.0.1:5000/todo/api/v1.0"


class TestSearchAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.test_client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_search_get_all(self):
        with self.app.test_client() as client:
            search_uri = f"{BASE_URL}/search"
            response = client.get(search_uri)
            data = json.loads(response.get_data())
            self.assertEqual(response.status_code, 200)

    def test_search_post(self):
        with self.app.test_client() as client:
            search_uri = f"{BASE_URL}/search"
            json_data_1 = {
                'search_field': {
                    'q': {
                        'author': 'ShamsCharania'
                    }
                }
            }
            response = client.post(
                search_uri,
                data=json.dumps(json_data_1),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)

            json_data_2 = {
                'search_field': {
                    'q': {
                        'author': 'wojespn'
                    }
                }
            }
            response = client.post(
                search_uri,
                data=json.dumps(json_data_2),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)

            json_data_3 = {
                'search_field': {
                    'q': {
                        'author': 'ZachLowe_NBA'
                    }
                }
            }
            response = client.post(
                search_uri,
                data=json.dumps(json_data_3),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)

    def test_search_get_one(self):
        with self.app.test_client() as client:
            search_uri = f"{BASE_URL}/search"
            json_data = {
                'search_field': {
                    'q': {
                        'author': 'ShamsCharania'
                    }
                }
            }
            response = client.post(
                search_uri,
                data=json.dumps(json_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)

            search_uri = f"{BASE_URL}/search/1"
            response = client.get(search_uri)
            self.assertEqual(response.status_code, 200)

            search_uri = f"{BASE_URL}/search/4"
            response = client.get(search_uri)
            self.assertEqual(response.status_code, 404)

    def test_search_put(self):
        pass

    def test_search_delete(self):
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
