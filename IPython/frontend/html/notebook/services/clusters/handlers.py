"""Tornado handlers for cluster web service.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from tornado import web

from zmq.utils import jsonapi

from ...base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Cluster handlers
#-----------------------------------------------------------------------------


class MainClusterHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        self.finish(jsonapi.dumps(self.cluster_manager.list_profiles()))


class ClusterProfileHandler(IPythonHandler):

    @web.authenticated
    def get(self, profile):
        self.finish(jsonapi.dumps(self.cluster_manager.profile_info(profile)))


class ClusterActionHandler(IPythonHandler):

    @web.authenticated
    def post(self, profile, action):
        cm = self.cluster_manager
        if action == 'start':
            n = self.get_argument('n', default=None)
            if not n:
                data = cm.start_cluster(profile)
            else:
                data = cm.start_cluster(profile, int(n))
        if action == 'stop':
            data = cm.stop_cluster(profile)
        self.finish(jsonapi.dumps(data))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_cluster_action_regex = r"(?P<action>start|stop)"
_profile_regex = r"(?P<profile>[^\/]+)" # there is almost no text that is invalid

default_handlers = [
    (r"/clusters", MainClusterHandler),
    (r"/clusters/%s/%s" % (_profile_regex, _cluster_action_regex), ClusterActionHandler),
    (r"/clusters/%s" % _profile_regex, ClusterProfileHandler),
]
