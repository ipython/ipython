""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os

static_dir = 'static'
components_dir = os.path.join(static_dir,'components')

def test_component(name):
    if not os.path.exists(os.path.join(components_dir,name)):
        components()

def components():
    """install components with bower"""
    with lcd(static_dir):
        local('bower install')

def css(minify=True):
    """generate the css from less files"""
    test_component('bootstrap')
    test_component('less.js')
    if minify not in ['True', 'False', True, False]:
        abort('minify must be Boolean')
    minify = (minify in ['True',True])

    min_flag= '-x' if minify is True else ''
    with lcd(static_dir):
        local('lessc {min_flag} less/style.less css/style.min.css'.format(min_flag=min_flag))

