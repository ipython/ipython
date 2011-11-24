"""Simple utility for building a list of local IPs using the socket module.
This module defines two constants:

LOCALHOST : The loopback interface, or the first interface that points to this
            machine.  It will *almost* always be '127.0.0.1'

LOCAL_IPS : A list of IP addresses, loopback first, that point to this machine.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import socket

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

LOCAL_IPS = []
try:
    LOCAL_IPS = socket.gethostbyname_ex('localhost')[2]
except socket.gaierror:
    pass

try:
    LOCAL_IPS.extend(socket.gethostbyname_ex(socket.gethostname())[2])
except socket.gaierror:
    pass

# include all-interface aliases: 0.0.0.0 and ''
LOCAL_IPS.extend(['0.0.0.0', ''])

LOCALHOST = LOCAL_IPS[0]
