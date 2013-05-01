""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os

static_dir = 'static'
components_dir = os.path.join(static_dir, 'components')


def css(minify=True):
    """generate the css from less files"""
    if minify not in ['True', 'False', True, False]:
        abort('minify must be Boolean')
    minify = (minify in ['True',True])

    min_flag= '-x' if minify is True else ''
    with lcd(static_dir):
        local('lessc {min_flag} less/style.less css/style.min.css'.format(min_flag=min_flag))

