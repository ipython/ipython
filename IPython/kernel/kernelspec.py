import io
import json
import os
import sys

pjoin = os.path.join

from IPython.utils.path import get_ipython_dir
from IPython.utils.py3compat import PY3
from IPython.utils.traitlets import HasTraits, List, Unicode

USER_KERNEL_DIR = pjoin(get_ipython_dir(), 'kernels')

if os.name == 'nt':
    programdata = os.environ.get('PROGRAMDATA', None)
    if programdata:
        SYSTEM_KERNEL_DIR = pjoin(programdata, 'ipython', 'kernels')
    else:  # PROGRAMDATA is not defined by default on XP.
        SYSTEM_KERNEL_DIR = None
else:
    SYSTEM_KERNEL_DIR = "/usr/share/ipython/kernels"
    
NATIVE_KERNEL_NAME = 'python3' if PY3 else 'python2'

class KernelSpec(HasTraits):
    argv = List()
    display_name = Unicode()
    language = Unicode()
    codemirror_mode = Unicode()
    
    resource_dir = Unicode()
    
    def __init__(self, resource_dir, argv, display_name, language,
                 codemirror_mode=None):
        super(KernelSpec, self).__init__(resource_dir=resource_dir, argv=argv,
                display_name=display_name, language=language,
                codemirror_mode=codemirror_mode)
        if not self.codemirror_mode:
            self.codemirror_mode = self.language
    
    @classmethod
    def from_resource_dir(cls, resource_dir):
        kernel_file = os.path.join(resource_dir, 'kernel.json')
        with io.open(kernel_file, 'r', encoding='utf-8') as f:
            kernel_dict = json.load(f)
        return cls(resource_dir=resource_dir, **kernel_dict)

def _is_kernel_dir(path):
    return os.path.isdir(path) and os.path.isfile(pjoin(path, 'kernel.json'))

def _list_kernels_in(dir):
    if dir is None:
        return {}
    if not os.path.isdir(dir):
        os.makedirs(dir, mode=0o644)
    return {f.lower(): pjoin(dir, f) for f in os.listdir(dir)
                        if _is_kernel_dir(pjoin(dir, f))}

def _make_native_kernel_dir():
    path = pjoin(USER_KERNEL_DIR, NATIVE_KERNEL_NAME)
    os.mkdir(path)
    with io.open(pjoin(path, 'kernel.json'), 'w', encoding='utf-8') as f:
        json.dump({'argv':[NATIVE_KERNEL_NAME, '-c',
                           'from IPython.kernel.zmq.kernelapp import main; main()',
                            '-f', '{connection_file}'],
                   'display_name': 'Python 3' if PY3 else 'Python 2',
                   'language': 'python',
                   'codemirror_mode': {'name': 'python',
                                       'version': sys.version_info[0]},
                  },
                  f)
    # TODO: Copy icons into directory
    return path

def list_kernel_specs():
    """Returns a dict mapping kernels to resource directories."""
    d = _list_kernels_in(SYSTEM_KERNEL_DIR)
    d.update(_list_kernels_in(USER_KERNEL_DIR))
    
    if NATIVE_KERNEL_NAME not in d:
        d[NATIVE_KERNEL_NAME] = _make_native_kernel_dir()
    return d

def get_kernel_spec(kernel_name):
    """Returns a KernelSpec instance for the given kernel_name.
    
    Raises KeyError if the given kernel name is not found.
    """
    d = list_kernel_specs()
    resource_dir = d[kernel_name.lower()]
    return KernelSpec.from_resource_dir(resource_dir)