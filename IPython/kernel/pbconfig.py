# encoding: utf-8

"""Low level configuration for Twisted's Perspective Broker protocol."""

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

from twisted.spread import banana


#-------------------------------------------------------------------------------
# This is where you configure the size limit of the banana protocol that
# PB uses.  WARNING, this only works if you are NOT using cBanana, which is
# faster than banana.py.
#-------------------------------------------------------------------------------



#banana.SIZE_LIMIT = 640*1024           # The default of 640 kB
banana.SIZE_LIMIT = 10*1024*1024       # 10 MB
#banana.SIZE_LIMIT = 50*1024*1024       # 50 MB   
    
# This sets the size of chunks used when paging is used.    
CHUNK_SIZE = 64*1024
