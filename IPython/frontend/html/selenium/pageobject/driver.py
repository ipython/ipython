from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import time
import json
import os

config = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '../selenium.json')
settings = json.load(open(config, 'rb'))

port = settings['port']
uri = 'http://localhost:%d/' % port

_cache = {}

def driver():
    if not 'driver' in _cache:
        _cache['driver'] = webdriver.Firefox()

    return _cache['driver']
