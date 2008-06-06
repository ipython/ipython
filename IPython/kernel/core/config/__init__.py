# encoding: utf-8

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from IPython.external.configobj import ConfigObj
from IPython.config.api import ConfigObjManager

default_core_config = ConfigObj()
default_core_config['shell'] = dict(
    shell_class = 'IPython.kernel.core.interpreter.Interpreter',
    import_statement = ''
)

config_manager = ConfigObjManager(default_core_config, 'IPython.kernel.core.ini')