import io
import json
import os
import shutil
import sys

pjoin = os.path.join

from IPython.utils.path import get_ipython_dir
from IPython.utils.py3compat import PY3
from IPython.utils.traitlets import HasTraits, List, Unicode, Dict, Any, Set
from IPython.config import Configurable
from .launcher import make_ipkernel_cmd

if os.name == 'nt':
    programdata = os.environ.get('PROGRAMDATA', None)
    if programdata:
        SYSTEM_KERNEL_DIRS = [pjoin(programdata, 'jupyter', 'kernels')]
    else:  # PROGRAMDATA is not defined by default on XP.
        SYSTEM_KERNEL_DIRS = []
else:
    SYSTEM_KERNEL_DIRS = ["/usr/share/jupyter/kernels",
                          "/usr/local/share/jupyter/kernels",
                         ]
    
NATIVE_KERNEL_NAME = 'python3' if PY3 else 'python2'

def _pythonfirst(s):
    "Sort key function that will put strings starting with 'python' first."
    if s == NATIVE_KERNEL_NAME:
        return '  ' + s  # Two spaces to sort this first of all
    elif s.startswith('python'):
        # Space is not valid in kernel names, so this should sort first
        return ' ' + s
    return s

class KernelSpec(HasTraits):
    argv = List()
    display_name = Unicode()
    language = Unicode()
    env = Dict()
    resource_dir = Unicode()
    
    @classmethod
    def from_resource_dir(cls, resource_dir):
        """Create a KernelSpec object by reading kernel.json
        
        Pass the path to the *directory* containing kernel.json.
        """
        kernel_file = pjoin(resource_dir, 'kernel.json')
        with io.open(kernel_file, 'r', encoding='utf-8') as f:
            kernel_dict = json.load(f)
        return cls(resource_dir=resource_dir, **kernel_dict)
    
    def to_dict(self):
        d = dict(argv=self.argv,
                 env=self.env,
                 display_name=self.display_name,
                 language=self.language,
                )

        return d

    def to_json(self):
        return json.dumps(self.to_dict())

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

class KernelSpecManager(Configurable):
    ipython_dir = Unicode()
    def _ipython_dir_default(self):
        return get_ipython_dir()

    user_kernel_dir = Unicode()
    def _user_kernel_dir_default(self):
        return pjoin(self.ipython_dir, 'kernels')

    @property
    def env_kernel_dir(self):
        return pjoin(sys.prefix, 'share', 'jupyter', 'kernels')
    
    whitelist = Set(config=True,
        help="""Whitelist of allowed kernel names.
        
        By default, all installed kernels are allowed.
        """
    )
    kernel_dirs = List(
        help="List of kernel directories to search. Later ones take priority over earlier."    
    )
    def _kernel_dirs_default(self):
        dirs = SYSTEM_KERNEL_DIRS[:]
        if self.env_kernel_dir not in dirs:
            dirs.append(self.env_kernel_dir)
        dirs.append(self.user_kernel_dir)
        return dirs

    @property
    def _native_kernel_dict(self):
        """Makes a kernel directory for the native kernel.
        
        The native kernel is the kernel using the same Python runtime as this
        process. This will put its information in the user kernels directory.
        """
        return {
                'argv': make_ipkernel_cmd(),
                'display_name': 'Python %i' % (3 if PY3 else 2),
                'language': 'python',
               }

    @property
    def _native_kernel_resource_dir(self):
        return pjoin(os.path.dirname(__file__), 'resources')

    def find_kernel_specs(self):
        """Returns a dict mapping kernel names to resource directories."""
        d = {}
        for kernel_dir in self.kernel_dirs:
            d.update(_list_kernels_in(kernel_dir))

        d[NATIVE_KERNEL_NAME] = self._native_kernel_resource_dir
        if self.whitelist:
            # filter if there's a whitelist
            d = {name:spec for name,spec in d.items() if name in self.whitelist}
        return d
        # TODO: Caching?

    def get_kernel_spec(self, kernel_name):
        """Returns a :class:`KernelSpec` instance for the given kernel_name.
        
        Raises :exc:`NoSuchKernel` if the given kernel name is not found.
        """
        if kernel_name in {'python', NATIVE_KERNEL_NAME} and \
            (not self.whitelist or kernel_name in self.whitelist):
            return KernelSpec(resource_dir=self._native_kernel_resource_dir,
                              **self._native_kernel_dict)

        d = self.find_kernel_specs()
        try:
            resource_dir = d[kernel_name.lower()]
        except KeyError:
            raise NoSuchKernel(kernel_name)
        return KernelSpec.from_resource_dir(resource_dir)
    
    def _get_destination_dir(self, kernel_name, user=False):
        if user:
            return os.path.join(self.user_kernel_dir, kernel_name)
        else:
            if SYSTEM_KERNEL_DIRS:
                return os.path.join(SYSTEM_KERNEL_DIRS[-1], kernel_name)
            else:
                raise EnvironmentError("No system kernel directory is available")


    def install_kernel_spec(self, source_dir, kernel_name=None, user=False,
                            replace=False):
        """Install a kernel spec by copying its directory.
        
        If ``kernel_name`` is not given, the basename of ``source_dir`` will
        be used.
        
        If ``user`` is False, it will attempt to install into the systemwide
        kernel registry. If the process does not have appropriate permissions,
        an :exc:`OSError` will be raised.
        
        If ``replace`` is True, this will replace an existing kernel of the same
        name. Otherwise, if the destination already exists, an :exc:`OSError`
        will be raised.
        """
        if not kernel_name:
            kernel_name = os.path.basename(source_dir)
        kernel_name = kernel_name.lower()
        
        destination = self._get_destination_dir(kernel_name, user=user)

        if replace and os.path.isdir(destination):
            shutil.rmtree(destination)

        shutil.copytree(source_dir, destination)

    def install_native_kernel_spec(self, user=False):
        """Install the native kernel spec to the filesystem
        
        This allows a Python 3 frontend to use a Python 2 kernel, or vice versa.
        The kernelspec will be written pointing to the Python executable on
        which this is run.
        
        If ``user`` is False, it will attempt to install into the systemwide
        kernel registry. If the process does not have appropriate permissions, 
        an :exc:`OSError` will be raised.
        """
        path = self._get_destination_dir(NATIVE_KERNEL_NAME, user=user)
        os.makedirs(path, mode=0o755)
        with open(pjoin(path, 'kernel.json'), 'w') as f:
            json.dump(self._native_kernel_dict, f, indent=1)
        copy_from = self._native_kernel_resource_dir
        for file in os.listdir(copy_from):
            shutil.copy(pjoin(copy_from, file), path)
        return path

def find_kernel_specs():
    """Returns a dict mapping kernel names to resource directories."""
    return KernelSpecManager().find_kernel_specs()

def get_kernel_spec(kernel_name):
    """Returns a :class:`KernelSpec` instance for the given kernel_name.
    
    Raises KeyError if the given kernel name is not found.
    """
    return KernelSpecManager().get_kernel_spec(kernel_name)

def install_kernel_spec(source_dir, kernel_name=None, user=False, replace=False):
    return KernelSpecManager().install_kernel_spec(source_dir, kernel_name,
                                                    user, replace)

install_kernel_spec.__doc__ = KernelSpecManager.install_kernel_spec.__doc__

def install_native_kernel_spec(user=False):
    return KernelSpecManager().install_native_kernel_spec(user=user)

install_native_kernel_spec.__doc__ = KernelSpecManager.install_native_kernel_spec.__doc__
