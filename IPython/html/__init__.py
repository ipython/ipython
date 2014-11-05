"""The IPython HTML Notebook"""

import os
# Packagers: modify this line if you store the notebook static files elsewhere
DEFAULT_STATIC_FILES_PATH = os.path.join(os.path.dirname(__file__), "static")
# Packagers: modify this line if you store the notebook template files elsewhere
DEFAULT_TEMPLATE_FILES_PATH = os.path.join(os.path.dirname(__file__), "templates")

del os

from .nbextensions import install_nbextension
