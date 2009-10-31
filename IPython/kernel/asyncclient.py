#!/usr/bin/env python
# encoding: utf-8

"""Asynchronous clients for the IPython controller.

This module has clients for using the various interfaces of the controller 
in a fully asynchronous manner.  This means that you will need to run the
Twisted reactor yourself and that all methods of the client classes return
deferreds to the result.

The main methods are are `get_*_client` and `get_client`.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.kernel import codeutil
from IPython.kernel.clientconnector import (
    AsyncClientConnector,
    AsyncCluster
)

# Other things that the user will need
from IPython.kernel.task import MapTask, StringTask
from IPython.kernel.error import CompositeError

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

_client_tub = AsyncClientConnector()
get_multiengine_client = _client_tub.get_multiengine_client
get_task_client = _client_tub.get_task_client
get_client = _client_tub.get_client

