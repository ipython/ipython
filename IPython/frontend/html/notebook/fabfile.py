""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os

static_dir = 'static'
components_dir = os.path.join(static_dir, 'components')
to_compile = [
    ('notebooks', 'style.less'),
    ('tree', 'style.less'),
    ('auth', 'style.less')
]

def css(minify=True):
    """generate the css from less files"""
    for subdir, filename in to_compile:
        _compile_less(subdir, filename, minify=minify)


def _compile_less(subdir, filename, minify=True):
    if minify not in ['True', 'False', True, False]:
        abort('minify must be Boolean')
    minify = (minify in ['True',True])
    min_flag= '-x' if minify is True else ''
    lessc = os.path.join('components', 'less.js', 'bin', 'lessc')

    source = os.path.join(subdir, 'less', filename)
    target = os.path.join(subdir, 'css', filename.replace('.less','.min.css'))
    subdir = os.path.join(static_dir, subdir)
    with lcd(static_dir):
        local('{lessc} {min_flag} {source} {target}'.format(**locals()))

