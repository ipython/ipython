"""Manager to read and modify frontend config data in JSON files.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from IPython.config.manager import BaseConfigManager

class ConfigManager(BaseConfigManager):
    """Config Manager use for storin Javascript side config"""

    def _config_dir(self):
        return os.path.join(self.profile_dir, 'nbconfig')
