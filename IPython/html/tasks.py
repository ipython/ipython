"""invoke task file to build CSS/JS"""

import os
from contextlib import contextmanager
from distutils.version import LooseVersion as V
from subprocess import check_output

from invoke import task, run

pjoin = os.path.join
static_dir = 'static'
components_dir = pjoin(static_dir, 'components')
here = os.path.dirname(__file__)

min_less_version = '1.7.5'
max_less_version = '1.8.0' # exclusive

@contextmanager
def lcd(path):
    """Context manager for setting CWD"""
    cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(cwd)


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
    
    # pin less to version number from above
    try:
        out = check_output(['lessc', '--version'])
    except OSError as err:
        raise ValueError("Unable to find lessc.  Please install lessc >= %s and < %s " \
                         % (min_less_version, max_less_version))
    out = out.decode('utf8', 'replace')
    less_version = out.split()[1]
    if V(less_version) < V(min_less_version):
        raise ValueError("lessc too old: %s < %s. Use `$ npm install lesscss@X.Y.Z` to install a specific version of less" % (less_version, min_less_version))
    if V(less_version) >= V(max_less_version):
        raise ValueError("lessc too new: %s >= %s. Use `$ npm install lesscss@X.Y.Z` to install a specific version of less" % (less_version, max_less_version))
    
    static_path = pjoin(here, static_dir)
    with lcd(static_path):
        run('lessc {min_flag} {ver_flag} --source-map={sourcemap} --source-map-basepath={static_path} --source-map-rootpath="../" {source} {target}'.format(**locals()),
            echo=True,
        )

def _rjs(name):
    with lcd(here):
        run("r.js -o build.js 'name={name}' 'out=static/{name}.min.js'".format(name=name))

@task
def js():
    """Compile minified javascript"""
    try:
        out = check_output(['r.js', '-v'])
    except OSError as err:
        raise ValueError("Unable to find r.js.  Please install with `npm install -g requirejs`")
    
    for name in ['notebook', 'tree']:
        _rjs(pjoin(name, 'js', 'main'))

    for name in ['logout', 'login']:
        _rjs(pjoin('auth', 'js', name + 'main'))

