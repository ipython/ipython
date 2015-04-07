"""The IPython kernel spec for Jupyter"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os
import shutil
import sys
import tempfile

from jupyter_client.kernelspec import KernelSpecManager

pjoin = os.path.join

KERNEL_NAME = 'python%i' % sys.version_info[0]

# path to kernelspec resources
RESOURCES = pjoin(os.path.dirname(__file__), 'resources')


def make_ipkernel_cmd(mod='ipython_kernel', executable=None, extra_arguments=[], **kw):
    """Build Popen command list for launching an IPython kernel.

    Parameters
    ----------
    mod : str, optional (default 'ipython_kernel')
        A string of an IPython module whose __main__ starts an IPython kernel

    executable : str, optional (default sys.executable)
        The Python executable to use for the kernel process.

    extra_arguments : list, optional
        A list of extra arguments to pass when executing the launch code.

    Returns
    -------

    A Popen command list
    """
    if executable is None:
        executable = sys.executable
    arguments = [ executable, '-m', mod, '-f', '{connection_file}' ]
    arguments.extend(extra_arguments)

    return arguments


def get_kernel_dict():
    """Construct dict for kernel.json"""
    return {
        'argv': make_ipkernel_cmd(),
        'display_name': 'Python %i' % sys.version_info[0],
        'language': 'python',
    }


def write_kernel_spec(path=None):
    """Write a kernel spec directory to `path`
    
    If `path` is not specified, a temporary directory is created.
    
    The path to the kernelspec is always returned.
    """
    if path is None:
        path = os.path.join(tempfile.mkdtemp(suffix='_kernels'), KERNEL_NAME)
    
    # stage resources
    shutil.copytree(RESOURCES, path)
    # write kernel.json
    with open(pjoin(path, 'kernel.json'), 'w') as f:
        json.dump(get_kernel_dict(), f, indent=1)
    
    return path


def install(kernel_spec_manager=None, user=False):
    """Install the IPython kernelspec for Jupyter
    
    Parameters
    ----------
    
    kernel_spec_manager: KernelSpecManager [optional]
        A KernelSpecManager to use for installation.
        If none provided, a default instance will be created.
    user: bool [default: False]
        Whether to do a user-only install, or system-wide.
    """
    if kernel_spec_manager is None:
        kernel_spec_manager = KernelSpecManager()
    path = write_kernel_spec()
    kernel_spec_manager.install_kernel_spec(path,
        kernel_name=KERNEL_NAME, user=user, replace=True)
    # cleanup afterward
    shutil.rmtree(path)
