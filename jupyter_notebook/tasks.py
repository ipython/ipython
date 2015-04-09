"""invoke task file to build CSS"""

from __future__ import print_function

import os
import sys
from distutils.version import LooseVersion as V
from subprocess import check_output

from invoke import task, run
from invoke.runner import Result
from invoke.exceptions import Failure

pjoin = os.path.join
static_dir = 'static'
components_dir = pjoin(static_dir, 'components')
here = os.path.dirname(__file__)

min_less_version = '2.0'
max_less_version = '3.0' # exclusive if string


def _fail(msg=''):
    """Fail a task, logging a message to stderr
    
    raises a special Failure Exception from invoke.
    """
    if msg:
        print(msg, file=sys.stderr)
    # raising a Failure allows us to avoid a traceback
    # we only care about exited, but stdout, stderr, pty are required args
    raise Failure(Result(stdout='', stderr='', pty=False, exited=1))

def _need_css_update():
    """Does less need to run?"""
    
    static_path = pjoin(here, static_dir)
    css_targets = [ 
        pjoin(static_path, 'style', '%s.min.css' % name)
        for name in ('style', 'ipython')
    ]
    css_maps = [t + '.map' for t in css_targets]
    targets = css_targets + css_maps
    if not all(os.path.exists(t) for t in targets):
        # some generated files don't exist
        return True
    earliest_target = sorted(os.stat(t).st_mtime for t in targets)[0]
    
    # check if any .less files are newer than the generated targets
    for (dirpath, dirnames, filenames) in os.walk(static_path):
        for f in filenames:
            if f.endswith('.less'):
                path = pjoin(static_path, dirpath, f)
                timestamp = os.stat(path).st_mtime
                if timestamp > earliest_target:
                    return True
    
    return False

@task
def css(minify=False, verbose=False, force=False):
    """generate the css from less files"""
    # minify implies force because it's not the default behavior
    if not force and not minify and not _need_css_update():
        print("css up-to-date")
        return
    
    for name in ('style', 'ipython'):
        source = pjoin('style', "%s.less" % name)
        target = pjoin('style', "%s.min.css" % name)
        sourcemap = pjoin('style', "%s.min.css.map" % name)
        _compile_less(source, target, sourcemap, minify, verbose)


def _compile_less(source, target, sourcemap, minify=True, verbose=False):
    """Compile a less file by source and target relative to static_dir"""
    min_flag = '-x' if minify else ''
    ver_flag = '--verbose' if verbose else ''
    
    install = "(npm install -g 'less@<{}')".format(max_less_version)
    # pin less to version number from above
    try:
        out = check_output(['lessc', '--version'])
    except OSError as err:
        _fail("Unable to find lessc.  Rebuilding css requires less >= {0} and < {1} {2}".format(
            min_less_version, max_less_version, install
        ))
    out = out.decode('utf8', 'replace')
    less_version = out.split()[1]
    if min_less_version and V(less_version) < V(min_less_version):
        _fail("lessc too old: {} < {} {}".format(
            less_version, min_less_version, install,
        ))
    if max_less_version and V(less_version) >= V(max_less_version):
        _fail("lessc too new: {} >= {} {}".format(
            less_version, max_less_version, install,
        ))
    
    static_path = pjoin(here, static_dir)
    cwd = os.getcwd()
    try:
        os.chdir(static_dir)
        run('lessc {min_flag} {ver_flag} --source-map={sourcemap} --source-map-basepath={static_path} --source-map-rootpath="../" {source} {target}'.format(**locals()),
            echo=True,
        )
    finally:
        os.chdir(cwd)

