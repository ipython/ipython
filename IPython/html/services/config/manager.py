"""Manager to read and modify frontend config data in JSON files.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.config.manager import BaseJSONConfigManager
from IPython.utils.path import locate_profile
from IPython.utils.traitlets import Unicode

class ConfigManager(BaseJSONConfigManager):
    """Config Manager used for storing notebook frontend config"""
    
    profile = Unicode('default', config=True)
    
    profile_dir = Unicode(config=True)
    
    def _profile_dir_default(self):
        return locate_profile(self.profile)

    def _config_dir_default(self):
        return self.profile_dir
