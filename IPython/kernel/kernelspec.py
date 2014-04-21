import io
import json
import os
import sys

pjoin = os.path.join

from IPython.utils.path import get_ipython_dir
from IPython.utils.py3compat import PY3
from IPython.utils.traitlets import HasTraits, List, Unicode, Dict

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
    codemirror_mode = None
    env = Dict()
    
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
        """Create a KernelSpec object by reading kernel.json
        
        Pass the path to the *directory* containing kernel.json.
        """
        kernel_file = pjoin(resource_dir, 'kernel.json')
        with io.open(kernel_file, 'r', encoding='utf-8') as f:
            kernel_dict = json.load(f)
        return cls(resource_dir=resource_dir, **kernel_dict)

def _is_kernel_dir(path):
    """Is ``path`` a kernel directory?"""
    return os.path.isdir(path) and os.path.isfile(pjoin(path, 'kernel.json'))

def _list_kernels_in(dir):
    """Return a mapping of kernel names to resource directories from dir.
    
    If dir is None or does not exist, returns an empty dict.
    """
    if dir is None or not os.path.isdir(dir):
        return {}
    return {f.lower(): pjoin(dir, f) for f in os.listdir(dir)
                        if _is_kernel_dir(pjoin(dir, f))}

class NoSuchKernel(KeyError):
    def __init__(self, name):
        self.name = name

class KernelSpecManager(HasTraits):
    ipython_dir = Unicode()
    def _ipython_dir_default(self):
        return get_ipython_dir()

    user_kernel_dir = Unicode()
    def _user_kernel_dir_default(self):
        return pjoin(self.ipython_dir, 'kernels')
    
    kernel_dirs = List(
        help="List of kernel directories to search. Later ones take priority over earlier."    
    )    
    def _kernel_dirs_default(self):
        return [
            SYSTEM_KERNEL_DIR,
            self.user_kernel_dir,
        ]

    def _make_native_kernel_dir(self):
        """Makes a kernel directory for the native kernel.
        
        The native kernel is the kernel using the same Python runtime as this
        process. This will put its informatino in the user kernels directory.
        """
        path = pjoin(self.user_kernel_dir, NATIVE_KERNEL_NAME)
        os.makedirs(path, mode=0o755)
        with open(pjoin(path, 'kernel.json'), 'w') as f:
            json.dump({'argv':[NATIVE_KERNEL_NAME, '-c',
                               'from IPython.kernel.zmq.kernelapp import main; main()',
                                '-f', '{connection_file}'],
                       'display_name': 'Python 3' if PY3 else 'Python 2',
                       'language': 'python',
                       'codemirror_mode': {'name': 'python',
                                           'version': sys.version_info[0]},
                      },
                      f, indent=1)
        # TODO: Copy icons into directory
        return path
    
    def find_kernel_specs(self):
        """Returns a dict mapping kernel names to resource directories."""
        d = {}
        for kernel_dir in self.kernel_dirs:
            d.update(_list_kernels_in(kernel_dir))
        
        if NATIVE_KERNEL_NAME not in d:
            d[NATIVE_KERNEL_NAME] = self._make_native_kernel_dir()
        return d
        # TODO: Caching?
    
    def get_kernel_spec(self, kernel_name):
        """Returns a :class:`KernelSpec` instance for the given kernel_name.
        
        Raises :exc:`NoSuchKernel` if the given kernel name is not found.
        """
        if kernel_name == 'python':
            kernel_name = NATIVE_KERNEL_NAME
        d = self.find_kernel_specs()
        try:
            resource_dir = d[kernel_name.lower()]
        except KeyError:
            raise NoSuchKernel(kernel_name)
        return KernelSpec.from_resource_dir(resource_dir)

def find_kernel_specs():
    """Returns a dict mapping kernel names to resource directories."""
    return KernelSpecManager().find_kernel_specs()

def get_kernel_spec(kernel_name):
    """Returns a :class:`KernelSpec` instance for the given kernel_name.
    
    Raises KeyError if the given kernel name is not found.
    """
    return KernelSpecManager().get_kernel_spec(kernel_name)