"""Tornado handlers for cluster web service."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json

from tornado import web

from ...base.handlers import APIHandler

#-----------------------------------------------------------------------------
# Cluster handlers
#-----------------------------------------------------------------------------


class MainClusterHandler(APIHandler):

    @web.authenticated
    def get(self):
        self.finish(json.dumps(self.cluster_manager.list_profiles()))


class ClusterProfileHandler(APIHandler):

    @web.authenticated
    def get(self, profile):
        self.finish(json.dumps(self.cluster_manager.profile_info(profile)))


class ClusterActionHandler(APIHandler):

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
        self.finish(json.dumps(data))


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
