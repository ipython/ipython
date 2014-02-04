""" fabfile to prepare the notebook """

from fabric.api import local,lcd
from fabric.utils import abort
import os
from distutils.version import LooseVersion as V
from subprocess import check_output

pjoin = os.path.join
static_dir = 'static'
components_dir = os.path.join(static_dir, 'components')

min_less_version = '1.4.0'
max_less_version = '1.5.0' # exclusive

def css(minify=True, verbose=False):
    """generate the css from less files"""
    for name in ('style', 'ipython'):
        source = pjoin('style', "%s.less" % name)
        target = pjoin('style', "%s.min.css" % name)
        _compile_less(source, target, minify, verbose)

def _to_bool(b):
    if not b in ['True', 'False', True, False]:
        abort('boolean expected, got: %s' % b)
    return (b in ['True', True])

def _compile_less(source, target, minify=True, verbose=False):
    """Compile a less file by source and target relative to static_dir"""
    minify = _to_bool(minify)
    verbose = _to_bool(verbose)
    min_flag = '-x' if minify is True else ''
    ver_flag = '--verbose' if verbose is True else ''
    
    # pin less to 1.4
    out = check_output(['lessc', '--version'])
    out = out.decode('utf8', 'replace')
    less_version = out.split()[1]
    if V(less_version) < V(min_less_version):
        raise ValueError("lessc too old: %s < %s" % (less_version, min_less_version))
    if V(less_version) > V(max_less_version):
        raise ValueError("lessc too new: %s > %s" % (less_version, max_less_version))
    
    with lcd(static_dir):
        local('lessc {min_flag} {ver_flag} {source} {target}'.format(**locals()))

