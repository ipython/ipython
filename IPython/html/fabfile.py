""" fabfile to prepare the notebook """
import os
from fabric.api import local,lcd
from fabric.utils import abort
from distutils.version import LooseVersion as V
from subprocess import check_output

pjoin = os.path.join
static_dir = 'static'
components_dir = os.path.join(static_dir, 'components')

min_less_version = '1.7.0'
max_less_version = '1.8.0' # exclusive
min_rjs_version = '2.1.13'

def js(minify=True, verbose=False):
    """Optimize IPython JS"""
    _optimize_js(pjoin('widgets', 'js', 'build.js'), minify, verbose)

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

def css(minify=False, verbose=False, force=False):
    """generate the css from less files"""
    minify = _to_bool(minify)
    verbose = _to_bool(verbose)
    force = _to_bool(force)
    # minify implies force because it's not the default behavior
    if not force and not minify and not _need_css_update():
        print("css up-to-date")
        return
    
    for name in ('style', 'ipython'):
        source = pjoin('style', "%s.less" % name)
        target = pjoin('style', "%s.min.css" % name)
        sourcemap = pjoin('style', "%s.min.css.map" % name)
        _compile_less(source, target, sourcemap, minify, verbose)

def _to_bool(b):
    if not b in ['True', 'False', True, False]:
        abort('boolean expected, got: %s' % b)
    return (b in ['True', True])

def _compile_less(source, target, sourcemap, minify=True, verbose=False):
    """Compile a less file by source and target relative to static_dir"""
    min_flag = '-x' if minify is True else ''
    ver_flag = '--verbose' if verbose is True else ''
    
    # Validate less version
    try:
        out = local('lessc --version', capture=True)
    except OSError as err:
        raise ValueError("Unable to find lessc.  Please install lessc >= %s and < %s " \
                         % (min_less_version, max_less_version))
    less_version = out.split()[1]
    if V(less_version) < V(min_less_version):
        raise ValueError("lessc too old: %s < %s. Use `$ npm install less@X.Y.Z` to install a specific version of less" % (less_version, min_less_version))
    if V(less_version) >= V(max_less_version):
        raise ValueError("lessc too new: %s >= %s. Use `$ npm install less@X.Y.Z` to install a specific version of less" % (less_version, max_less_version))
    
    static_path = pjoin(here, static_dir)
    with lcd(static_dir):
        local('lessc {min_flag} {ver_flag} --source-map={sourcemap} --source-map-basepath={static_path} --source-map-rootpath="../" {source} {target}'.format(**locals()))

def _optimize_js(build_file, minify=True, verbose=False):
    """Optimizes a tree of require.js Javascript package files based on the
    contents of the provided build script."""
    minify = _to_bool(minify)
    verbose = _to_bool(verbose)
    min_flag = 'optimize=none' if minify is False else ''
    ver_flag = 'logLevel=2' if verbose is False else '' # 2 = WARNINGS ONLY

    # Validate r.js installation and version
    try:
        out = local('r.js -v', capture=True)
    except OSError as err:
        raise ValueError("Unable to find r.js.  Please install r.js >= %s" % min_rjs_version)
    version_info = {v[0].strip(): v[1].strip() for v in \
        [w.split(':') for w in out.lower().split(',')]}
    rjs_version = version_info['r.js']
    if not check_version(rjs_version, min_rjs_version):
        raise ValueError("r.js version {} is too old.  Please update your r.js" +
            "installation to >= {}".format(rjs_version, min_rjs_version))
    
    # Run the command
    with lcd(static_dir):
        local('r.js -o {build_file} {min_flag} {ver_flag}'.format(**locals()))
