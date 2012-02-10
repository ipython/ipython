"""Manage IPython.parallel clusters in the notebook.

Authors:

* Brian Granger
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

import datetime
import os
import uuid
import glob

from tornado import web
from zmq.eventloop import ioloop

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Unicode, List, Dict, Bool
from IPython.parallel.apps.launcher import IPClusterLauncher
from IPython.core.profileapp import list_profiles_in, list_bundled_profiles
from IPython.utils.path import get_ipython_dir, get_ipython_package_dir

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ClusterManager(LoggingConfigurable):

    profiles = Dict()


    def list_profile_names(self):
        """List all profiles in the ipython_dir and cwd.
        """
        profiles = list_profiles_in(get_ipython_dir())
        profiles += list_profiles_in(os.getcwdu())
        return profiles


    def list_profiles(self):
        profiles = self.list_profile_names()
        result = [self.profile_info(p) for p in profiles]
        return result


    def profile_info(self, profile):
        if profile not in self.list_profile_names():
            raise web.HTTPError(404, u'profile not found')
        result = dict(profile=profile)
        data = self.profiles.get(profile)
        if data is None:
            result['status'] = 'stopped'
        else:
            result['status'] = 'running'
            result['n'] = data['n']
        return result

    def start_cluster(self, profile, n=4):
        """Start a cluster for a given profile."""
        if profile not in self.list_profile_names():
            raise web.HTTPError(404, u'profile not found')
        if profile in self.profiles:
            raise web.HTTPError(409, u'cluster already running')
        launcher = IPClusterLauncher(ipcluster_profile=profile, ipcluster_n=n)
        launcher.start()
        self.profiles[profile] = {
            'launcher': launcher,
            'n': n
        }
        return self.profile_info(profile)

    def stop_cluster(self, profile):
        """Stop a cluster for a given profile."""
        if profile not in self.profiles:
            raise web.HTTPError(409, u'cluster not running')
        launcher = self.profiles.pop(profile)['launcher']
        launcher.stop()
        return self.profile_info(profile)

    def stop_all_clusters(self):
        for p in self.profiles.values():
            p['launcher'].stop()
