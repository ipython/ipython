"""Manage IPython.parallel clusters in the notebook."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Dict, Instance, Float
from IPython.core.profileapp import list_profiles_in
from IPython.core.profiledir import ProfileDir
from IPython.utils import py3compat
from IPython.utils.path import get_ipython_dir


class ClusterManager(LoggingConfigurable):

    profiles = Dict()

    delay = Float(1., config=True,
        help="delay (in s) between starting the controller and the engines")

    loop = Instance('zmq.eventloop.ioloop.IOLoop')
    def _loop_default(self):
        from zmq.eventloop.ioloop import IOLoop
        return IOLoop.instance()

    def build_launchers(self, profile_dir):
        from IPython.parallel.apps.ipclusterapp import IPClusterStart
        
        class DummyIPClusterStart(IPClusterStart):
            """Dummy subclass to skip init steps that conflict with global app.
    
            Instantiating and initializing this class should result in fully configured
            launchers, but no other side effects or state.
            """

            def init_signal(self):
                pass
            def reinit_logging(self):
                pass
        
        starter = DummyIPClusterStart(log=self.log)
        starter.initialize(['--profile-dir', profile_dir])
        cl = starter.controller_launcher
        esl = starter.engine_launcher
        n = starter.n
        return cl, esl, n

    def get_profile_dir(self, name, path):
        p = ProfileDir.find_profile_dir_by_name(path,name=name)
        return p.location

    def update_profiles(self):
        """List all profiles in the ipython_dir and cwd.
        """
        
        stale = set(self.profiles)
        for path in [get_ipython_dir(), py3compat.getcwd()]:
            for profile in list_profiles_in(path):
                if profile in stale:
                    stale.remove(profile)
                pd = self.get_profile_dir(profile, path)
                if profile not in self.profiles:
                    self.log.debug("Adding cluster profile '%s'", profile)
                    self.profiles[profile] = {
                        'profile': profile,
                        'profile_dir': pd,
                        'status': 'stopped'
                    }
        for profile in stale:
            # remove profiles that no longer exist
            self.log.debug("Profile '%s' no longer exists", profile)
            self.profiles.pop(profile)

    def list_profiles(self):
        self.update_profiles()
        # sorted list, but ensure that 'default' always comes first
        default_first = lambda name: name if name != 'default' else ''
        result = [self.profile_info(p) for p in sorted(self.profiles, key=default_first)]
        return result

    def check_profile(self, profile):
        if profile not in self.profiles:
            raise web.HTTPError(404, u'profile not found')

    def profile_info(self, profile):
        self.check_profile(profile)
        result = {}
        data = self.profiles.get(profile)
        result['profile'] = profile
        result['profile_dir'] = data['profile_dir']
        result['status'] = data['status']
        if 'n' in data:
            result['n'] = data['n']
        return result

    def start_cluster(self, profile, n=None):
        """Start a cluster for a given profile."""
        self.check_profile(profile)
        data = self.profiles[profile]
        if data['status'] == 'running':
            raise web.HTTPError(409, u'cluster already running')
        cl, esl, default_n = self.build_launchers(data['profile_dir'])
        n = n if n is not None else default_n
        def clean_data():
            data.pop('controller_launcher',None)
            data.pop('engine_set_launcher',None)
            data.pop('n',None)
            data['status'] = 'stopped'
        def engines_stopped(r):
            self.log.debug('Engines stopped')
            if cl.running:
                cl.stop()
            clean_data()
        esl.on_stop(engines_stopped)
        def controller_stopped(r):
            self.log.debug('Controller stopped')
            if esl.running:
                esl.stop()
            clean_data()
        cl.on_stop(controller_stopped)
        loop = self.loop
        
        def start():
            """start the controller, then the engines after a delay"""
            cl.start()
            loop.add_timeout(self.loop.time() + self.delay, lambda : esl.start(n))
        self.loop.add_callback(start)

        self.log.debug('Cluster started')
        data['controller_launcher'] = cl
        data['engine_set_launcher'] = esl
        data['n'] = n
        data['status'] = 'running'
        return self.profile_info(profile)

    def stop_cluster(self, profile):
        """Stop a cluster for a given profile."""
        self.check_profile(profile)
        data = self.profiles[profile]
        if data['status'] == 'stopped':
            raise web.HTTPError(409, u'cluster not running')
        data = self.profiles[profile]
        cl = data['controller_launcher']
        esl = data['engine_set_launcher']
        if cl.running:
            cl.stop()
        if esl.running:
            esl.stop()
        # Return a temp info dict, the real one is updated in the on_stop
        # logic above.
        result = {
            'profile': data['profile'],
            'profile_dir': data['profile_dir'],
            'status': 'stopped'
        }
        return result

    def stop_all_clusters(self):
        for p in self.profiles.keys():
            self.stop_cluster(p)
