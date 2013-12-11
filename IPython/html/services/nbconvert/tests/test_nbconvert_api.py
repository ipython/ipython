import requests

from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase

class NbconvertAPI(object):
    """Wrapper for nbconvert API calls."""
    def __init__(self, base_url):
        self.base_url = base_url

    def _req(self, verb, path, body=None, params=None):
        response = requests.request(verb,
                url_path_join(self.base_url, 'api/nbconvert', path),
                data=body, params=params,
        )
        response.raise_for_status()
        return response

    def list_formats(self):
        return self._req('GET', '')

class APITest(NotebookTestBase):
    def setUp(self):
        self.nbconvert_api = NbconvertAPI(self.base_url())

    def test_list_formats(self):
        formats = self.nbconvert_api.list_formats().json()
        self.assertIsInstance(formats, dict)
        self.assertIn('python', formats)
        self.assertIn('html', formats)
        self.assertEqual(formats['python']['output_mimetype'], 'text/x-python')