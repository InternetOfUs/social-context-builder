import unittest
from FlaskApp import app, views


class TestMyApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_social_relations(self):
        rv = self.app.get('/social/relations/U100046')
        assert rv.status == '200 OK'

    def test_social_explanation(self):
        rv = self.app.get('/social/explanations/U100047/T100093/')
        assert rv.status == '200 OK'

     
if __name__ == '__main__':
    unittest.main()