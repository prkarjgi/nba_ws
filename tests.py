from nba_ws import create_app, db
from config import TestingConfig
from typing import List, Tuple
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
        data = (
            {
                'search_field': {
                    'q': {
                        'author': 'wojespn'
                    }
                }
            },
            {
                'search_field': {
                    'q': {
                        'author': 'ShamsCharania'
                    }
                }
            }
        )
        self.add_search_fields(data)
        with self.app.test_client() as client:
            search_uri = f"{BASE_URL}/search"
            response = client.get(search_uri)
            data = json.loads(response.get_data())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data['search_fields']), 2)

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
        data = (
            {
                'search_field': {
                    'q': {
                        'author': 'wojespn'
                    }
                }
            },
        )
        self.add_search_fields(data)
        with self.app.test_client() as client:
            search_uri = f"{BASE_URL}/search/1"
            json_data = {
                'search_field': {
                    'q': {
                        'author': 'ShamsCharania'
                    }
                }
            }
            response = client.put(
                search_uri,
                data=json.dumps(json_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

    def test_search_delete(self):
        data = (
            {
                'search_field': {
                    'q': {
                        'author': 'wojespn'
                    }
                }
            },
            {
                'search_field': {
                    'q': {
                        'author': 'ShamsCharania'
                    }
                }
            }
        )
        self.add_search_fields(data)
        with self.app.test_client() as client:
            search_uri = f"{BASE_URL}/search/1"
            response = client.delete(
                search_uri
            )
            self.assertEqual(response.status_code, 200)

            response = client.get(
                search_uri
            )
            self.assertEqual(response.status_code, 404)

    def add_search_fields(self, search_fields: Tuple):
        search_uri = f"{BASE_URL}/search"
        with self.app.test_client() as client:
            for search_field in search_fields:
                response = client.post(
                    search_uri,
                    data=json.dumps(search_field),
                    content_type='application/json'
                )


def search_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestSearchAPI('test_search_get_all'))
    suite.addTest(TestSearchAPI('test_search_post'))
    suite.addTest(TestSearchAPI('test_search_get_one'))
    suite.addTest(TestSearchAPI('test_search_put'))
    suite.addTest(TestSearchAPI('test_search_delete'))
    return suite


def final_suite(test_suites: Tuple):
    final_suite = unittest.TestSuite()
    final_suite.addTests(test_suites)
    return final_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(final_suite((search_suite(),)))
