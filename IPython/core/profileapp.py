# encoding: utf-8
"""
An application for managing IPython profiles.

To be invoked as the `ipython profile` subcommand.

Authors:

* Min RK

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
import os

from IPython.config.application import Application, boolean_flag
from IPython.core.application import (
    BaseIPythonApplication, base_flags, base_aliases
)
from IPython.core.profiledir import ProfileDir
from IPython.utils.path import get_ipython_dir, get_ipython_package_dir
from IPython.utils.traitlets import Unicode, Bool, Dict

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

create_help = """Create an IPython profile by name

Create an ipython profile directory by its name or
profile directory path. Profile directories contain
configuration, log and security related files and are named
using the convention 'profile_<name>'. By default they are
located in your ipython directory. Once created, you will
can edit the configuration files in the profile
directory to configure IPython. Most users will create a
profile directory by name,
`ipython profile create myprofile`, which will put the directory
in `<ipython_dir>/profile_myprofile`.
"""
list_help = """List available IPython profiles

List all available profiles, by profile location, that can
be found in the current working directly or in the ipython
directory. Profile directories are named using the convention
'profile_<profile>'.
"""
profile_help = """Manage IPython profiles

Profile directories contain
configuration, log and security related files and are named
using the convention 'profile_<name>'. By default they are
located in your ipython directory.  You can create profiles
with `ipython profile create <name>`, or see the profiles you
already have with `ipython profile list`

To get started configuring IPython, simply do:

$> ipython profile create

and IPython will create the default profile in <ipython_dir>/profile_default,
where you can edit ipython_config.py to start configuring IPython.

"""

_list_examples = "ipython profile list  # list all profiles"

_create_examples = """
ipython profile create foo         # create profile foo w/ default config files
ipython profile create foo --reset # restage default config files over current
ipython profile create foo --parallel # also stage parallel config files
"""

_main_examples = """
ipython profile create -h  # show the help string for the create subcommand
ipython profile list -h    # show the help string for the list subcommand
"""

#-----------------------------------------------------------------------------
# Profile Application Class (for `ipython profile` subcommand)
#-----------------------------------------------------------------------------


class ProfileList(Application):
    name = u'ipython-profile'
    description = list_help
    examples = _list_examples

    aliases = Dict({
        'ipython-dir' : 'ProfileList.ipython_dir',
        'log-level' : 'Application.log_level',
    })
    flags = Dict(dict(
        debug = ({'Application' : {'log_level' : 0}},
            "Set Application.log_level to 0, maximizing log output."
        )
    ))

    ipython_dir = Unicode(get_ipython_dir(), config=True,
        help="""
        The name of the IPython directory. This directory is used for logging
        configuration (through profiles), history storage, etc. The default
        is usually $HOME/.ipython. This options can also be specified through
        the environment variable IPYTHON_DIR.
        """
    )
    
    def _list_profiles_in(self, path):
        """list profiles in a given root directory"""
        files = os.listdir(path)
        profiles = []
        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path) and f.startswith('profile_'):
                profiles.append(f.split('_',1)[-1])
        return profiles
    
    def _list_bundled_profiles(self):
        """list profiles in a given root directory"""
        path = os.path.join(get_ipython_package_dir(), u'config', u'profile')
        files = os.listdir(path)
        profiles = []
        for profile in files:
            full_path = os.path.join(path, profile)
            if os.path.isdir(full_path):
                profiles.append(profile)
        return profiles
    
    def _print_profiles(self, profiles):
        """print list of profiles, indented."""
        for profile in profiles:
            print '    %s' % profile
    
    def list_profile_dirs(self):
        profiles = self._list_bundled_profiles()
        if profiles:
            print
            print "Available profiles in IPython:"
            self._print_profiles(profiles)
            print
            print "    The first request for a bundled profile will copy it"
            print "    into your IPython directory (%s)," % self.ipython_dir
            print "    where you can customize it."
        
        profiles = self._list_profiles_in(self.ipython_dir)
        if profiles:
            print
            print "Available profiles in %s:" % self.ipython_dir
            self._print_profiles(profiles)
        
        profiles = self._list_profiles_in(os.getcwdu())
        if profiles:
            print
            print "Available profiles in current directory (%s):" % os.getcwdu()
            self._print_profiles(profiles)
        
        print
        print "To use any of the above profiles, start IPython with:"
        print "    ipython --profile=<name>"
        print

    def start(self):
        self.list_profile_dirs()


create_flags = {}
create_flags.update(base_flags)
# don't include '--init' flag, which implies running profile create in other apps
create_flags.pop('init')
create_flags['reset'] = ({'ProfileCreate': {'overwrite' : True}},
                        "reset config files in this profile to the defaults.")
create_flags['parallel'] = ({'ProfileCreate': {'parallel' : True}},
                        "Include the config files for parallel "
                        "computing apps (ipengine, ipcontroller, etc.)")


class ProfileCreate(BaseIPythonApplication):
    name = u'ipython-profile'
    description = create_help
    examples = _create_examples
    auto_create = Bool(True, config=False)

    def _copy_config_files_default(self):
        return True

    parallel = Bool(False, config=True,
        help="whether to include parallel computing config files")
    def _parallel_changed(self, name, old, new):
        parallel_files = [   'ipcontroller_config.py',
                            'ipengine_config.py',
                            'ipcluster_config.py'
                        ]
        if new:
            for cf in parallel_files:
                self.config_files.append(cf)
        else:
            for cf in parallel_files:
                if cf in self.config_files:
                    self.config_files.remove(cf)

    def parse_command_line(self, argv):
        super(ProfileCreate, self).parse_command_line(argv)
        # accept positional arg as profile name
        if self.extra_args:
            self.profile = self.extra_args[0]

    flags = Dict(create_flags)

    classes = [ProfileDir]

    def init_config_files(self):
        super(ProfileCreate, self).init_config_files()
        # use local imports, since these classes may import from here
        from IPython.frontend.terminal.ipapp import TerminalIPythonApp
        apps = [TerminalIPythonApp]
        try:
            from IPython.frontend.qt.console.qtconsoleapp import IPythonQtConsoleApp
        except Exception:
            # this should be ImportError, but under weird circumstances
            # this might be an AttributeError, or possibly others
            # in any case, nothing should cause the profile creation to crash.
            pass
        else:
            apps.append(IPythonQtConsoleApp)
        try:
            from IPython.frontend.html.notebook.notebookapp import NotebookApp
        except ImportError:
            pass
        except Exception:
            self.log.debug('Unexpected error when importing NotebookApp',
                           exc_info=True
            )
        else:
            apps.append(NotebookApp)
        if self.parallel:
            from IPython.parallel.apps.ipcontrollerapp import IPControllerApp
            from IPython.parallel.apps.ipengineapp import IPEngineApp
            from IPython.parallel.apps.ipclusterapp import IPClusterStart
            from IPython.parallel.apps.iploggerapp import IPLoggerApp
            apps.extend([
                IPControllerApp,
                IPEngineApp,
                IPClusterStart,
                IPLoggerApp,
            ])
        for App in apps:
            app = App()
            app.config.update(self.config)
            app.log = self.log
            app.overwrite = self.overwrite
            app.copy_config_files=True
            app.profile = self.profile
            app.init_profile_dir()
            app.init_config_files()

    def stage_default_config_file(self):
        pass


class ProfileApp(Application):
    name = u'ipython-profile'
    description = profile_help
    examples = _main_examples

    subcommands = Dict(dict(
        create = (ProfileCreate, "Create a new profile dir with default config files"),
        list = (ProfileList, "List existing profiles")
    ))

    def start(self):
        if self.subapp is None:
            print "No subcommand specified. Must specify one of: %s"%(self.subcommands.keys())
            print
            self.print_description()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()

