"""Simple utility for building a list of local IPs using the socket module.
This module defines two constants:

LOCALHOST : The loopback interface, or the first interface that points to this
            machine.  It will *almost* always be '127.0.0.1'

LOCAL_IPS : A list of IP addresses, loopback first, that point to this machine.

PUBLIC_IPS : A list of public IP addresses that point to this machine.
             Use these to tell remote clients where to find you.
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

from .data import uniq_stable

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

LOCAL_IPS = []
try:
    LOCAL_IPS = socket.gethostbyname_ex('localhost')[2]
except socket.error:
    pass

PUBLIC_IPS = []
try:
    hostname = socket.gethostname()
    PUBLIC_IPS = socket.gethostbyname_ex(hostname)[2]
    # try hostname.local, in case hostname has been short-circuited to loopback
    if not hostname.endswith('.local') and all(ip.startswith('127') for ip in PUBLIC_IPS):
        PUBLIC_IPS = socket.gethostbyname_ex(socket.gethostname() + '.local')[2]
except socket.error:
    pass
else:
    PUBLIC_IPS = uniq_stable(PUBLIC_IPS)
    LOCAL_IPS.extend(PUBLIC_IPS)

# include all-interface aliases: 0.0.0.0 and ''
LOCAL_IPS.extend(['0.0.0.0', ''])

LOCAL_IPS = uniq_stable(LOCAL_IPS)

LOCALHOST = LOCAL_IPS[0]
