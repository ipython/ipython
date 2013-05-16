""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os

static_dir = 'static'
components_dir = os.path.join(static_dir, 'components')

def css(minify=True):
    """generate the css from less files"""
    source = os.path.join('style', 'style.less')
    target = os.path.join('style', 'style.min.css')
    _compile_less(source, target, minify)

def _compile_less(source, target, minify=True):
    """Complie a less file by source and target relative to static_dir"""
    if minify not in ['True', 'False', True, False]:
        abort('minify must be Boolean')
    minify = (minify in ['True',True])
    min_flag= '-x' if minify is True else ''
    lessc = os.path.join('components', 'less.js', 'bin', 'lessc')
    with lcd(static_dir):
        local('{lessc} {min_flag} {source} {target}'.format(**locals()))

