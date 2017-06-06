from driver import driver
d = driver()

import urlparse
import os
import json

_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '../selenium.json')
config = json.load(open(_config_file, 'rb'))

port = config['port']
uri = 'http://localhost:%d/' % port
locators = config['locators']

def find(element):
    from driver import driver
    return driver().find_element_by_id(locators[element])

class PageObject(object):
    def __init__(self, path):
        self._uri = urlparse.urljoin(uri, path)
        self.load()

    def load(self):
        d.get(self._uri)
