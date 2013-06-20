""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os

static_dir = 'static'
components_dir = os.path.join(static_dir, 'components')

def css(minify=True, verbose=False):
    """generate the css from less files"""
    source = os.path.join('style', 'style.less')
    target = os.path.join('style', 'style.min.css')
    _compile_less(source, target, minify, verbose)

def _to_bool(b):
    if not b in ['True', 'False', True, False]:
        abort('boolean expected, got: %s' % b)
    return (b in ['True', True])

def _compile_less(source, target, minify=True, verbose=False):
    """Complie a less file by source and target relative to static_dir"""
    minify = _to_bool(minify)
    verbose = _to_bool(verbose)
    min_flag = '-x' if minify is True else ''
    ver_flag = '--verbose' if verbose is True else ''
    lessc = os.path.join('components', 'less.js', 'bin', 'lessc')
    with lcd(static_dir):
        local('{lessc} {min_flag} {ver_flag} {source} {target}'.format(**locals()))

