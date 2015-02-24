"""Manager to read and modify frontend config data in JSON files.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from IPython.config.manager import BaseJSONConfigManager

class ConfigManager(BaseJSONConfigManager):
    """Config Manager used for storing notebook frontend config"""

    def _config_dir(self):
        return os.path.join(self.profile_dir, 'nbconfig')
