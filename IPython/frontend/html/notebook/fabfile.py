""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os

static_dir = 'static'
components_dir = os.path.join(static_dir,'components')

def test_component(name):
    if not os.path.exists(os.path.join(components_dir,name)):
        abort('cannot continue without component {}.'.format(name))


def css():
    """generate the css from less files"""
    test_component('bootstrap')
    test_component('less.js')
    with lcd(static_dir):
        local('lessc -x less/style.less css/style.min.css')

