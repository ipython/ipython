"""
build [and upload] Windows IPython releases

usage:

python tools/release_windows.py [--github] [--pypi]

Meant to be run on Windows

Requires that you have python and python3 on your PATH
"""

import glob
import os
import shutil
import sys

from toollib import sh
try:
    import gh_api
except ImportError:
    gh_api = None

github = '--github' in sys.argv

cmd_t = "{py} setup.py bdist_wininst --plat-name={plat}"

pypi = '--pypi' in sys.argv
pypi_cmd_t = "python setup.py upload_wininst -f {fname}"

for py in ['python', 'python3']:
    # deliberately mangle the name,
    # so easy_install doesn't find these and do horrible wrong things
    v = 3 if py.endswith('3') else 2
    try:
        shutil.rmtree('build')
    except OSError:
        pass
    for plat in ['win32', 'win-amd64']:
        cmd = cmd_t.format(**locals())
        sh(cmd)
        orig = glob.glob(os.path.join('dist', 'ipython-*.{plat}.exe'.format(**locals())))[0]
        mangled = orig.replace('.{plat}.exe'.format(**locals()),
                               '.py{v}-{plat}.exe'.format(**locals())
        )
        os.rename(orig, mangled)
        if pypi:
            sh(pypi_cmd_t.format(fname=mangled))
        if github and gh_api:
            print ("Uploading %s to GitHub" % mangled)
            desc = "IPython Installer for Python {v}.x on {plat}".format(**locals())
            gh_api.post_download('ipython/ipython', mangled, description=desc)
