
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import errno
import os.path

from IPython.config.application import Application
from IPython.core.application import (
    BaseIPythonApplication, base_flags, base_aliases
)
from IPython.utils.traitlets import Instance, Dict, Unicode, Bool

from .kernelspec import KernelSpecManager, _pythonfirst

class ListKernelSpecs(BaseIPythonApplication):
    description = """List installed kernel specifications."""
    kernel_spec_manager = Instance(KernelSpecManager)

    # Not all of the base aliases are meaningful (e.g. profile)
    aliases = {k: base_aliases[k] for k in ['ipython-dir', 'log-level']}
    flags = {'debug': base_flags['debug'],}

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(parent=self, ipython_dir=self.ipython_dir)

    def start(self):
        print("Available kernels:")
        for kernelname in sorted(self.kernel_spec_manager.find_kernel_specs(),
                                 key=_pythonfirst):
            print("  %s" % kernelname)


class InstallKernelSpec(BaseIPythonApplication):
    description = """Install a kernel specification directory."""
    kernel_spec_manager = Instance(KernelSpecManager)

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(ipython_dir=self.ipython_dir)

    sourcedir = Unicode()
    kernel_name = Unicode("", config=True,
        help="Install the kernel spec with this name"
    )
    def _kernel_name_default(self):
        return os.path.basename(self.sourcedir)

    user = Bool(False, config=True,
        help="""
        Try to install the kernel spec to the per-user directory instead of
        the system or environment directory.
        """
    )
    replace = Bool(False, config=True,
        help="Replace any existing kernel spec with this name."
    )

    aliases = {'name': 'InstallKernelSpec.kernel_name'}
    for k in ['ipython-dir', 'log-level']:
        aliases[k] = base_aliases[k]

    flags = {'user': ({'InstallKernelSpec': {'user': True}},
                "Install to the per-user kernel registry"),
             'replace': ({'InstallKernelSpec': {'replace': True}},
                "Replace any existing kernel spec with this name."),
             'debug': base_flags['debug'],
            }

    def parse_command_line(self, argv):
        super(InstallKernelSpec, self).parse_command_line(argv)
        # accept positional arg as profile name
        if self.extra_args:
            self.sourcedir = self.extra_args[0]
        else:
            print("No source directory specified.")
            self.exit(1)

    def start(self):
        try:
            self.kernel_spec_manager.install_kernel_spec(self.sourcedir,
                                                 kernel_name=self.kernel_name,
                                                 user=self.user,
                                                 replace=self.replace,
                                                )
        except OSError as e:
            if e.errno == errno.EACCES:
                print("Permission denied")
                self.exit(1)
            elif e.errno == errno.EEXIST:
                print("A kernel spec is already present at %s" % e.filename)
                self.exit(1)
            raise

class InstallNativeKernelSpec(BaseIPythonApplication):
    description = """Install the native kernel spec directory for this Python."""
    kernel_spec_manager = Instance(KernelSpecManager)

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(ipython_dir=self.ipython_dir)

    user = Bool(False, config=True,
        help="""
        Try to install the kernel spec to the per-user directory instead of
        the system or environment directory.
        """
    )

    # Not all of the base aliases are meaningful (e.g. profile)
    aliases = {k: base_aliases[k] for k in ['ipython-dir', 'log-level']}
    flags = {'user': ({'InstallNativeKernelSpec': {'user': True}},
                "Install to the per-user kernel registry"),
             'debug': base_flags['debug'],
            }

    def start(self):
        try:
            self.kernel_spec_manager.install_native_kernel_spec(user=self.user)
        except OSError as e:
            self.exit(e)

class KernelSpecApp(Application):
    name = "ipython kernelspec"
    description = """Manage IPython kernel specifications."""

    subcommands = Dict({
        'list': (ListKernelSpecs, ListKernelSpecs.description.splitlines()[0]),
        'install': (InstallKernelSpec, InstallKernelSpec.description.splitlines()[0]),
        'install-self': (InstallNativeKernelSpec, InstallNativeKernelSpec.description.splitlines()[0]),
    })

    aliases = {}
    flags = {}

    def start(self):
        if self.subapp is None:
            print("No subcommand specified. Must specify one of: %s"% list(self.subcommands))
            print()
            self.print_description()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()
