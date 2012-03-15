from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys as keys

_cache = {}

def driver():
    if not 'driver' in _cache:
        _cache['driver'] = webdriver.Firefox()

    return _cache['driver']

def wait(condition):
    WebDriverWait(driver(), 10).until(condition)
