# encoding: utf-8

"""Classes used in scattering and gathering sequences.

Scattering consists of partitioning a sequence and sending the various
pieces to individual nodes in a cluster.
"""

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

import types

from IPython.genutils import flatten as genutil_flatten

#-------------------------------------------------------------------------------
# Figure out which array packages are present and their array types
#-------------------------------------------------------------------------------

arrayModules = []
try:
    import Numeric
except ImportError:
    pass
else:
    arrayModules.append({'module':Numeric, 'type':Numeric.arraytype})
try:
    import numpy
except ImportError:
    pass
else:
    arrayModules.append({'module':numpy, 'type':numpy.ndarray})
try:
    import numarray
except ImportError:
    pass
else:
    arrayModules.append({'module':numarray,
        'type':numarray.numarraycore.NumArray})

class Map:
    """A class for partitioning a sequence using a map."""
            
    def getPartition(self, seq, p, q):
        """Returns the pth partition of q partitions of seq."""
        
        # Test for error conditions here
        if p<0 or p>=q:
          print "No partition exists."
          return
          
        remainder = len(seq)%q
        basesize = len(seq)/q
        hi = []
        lo = []
        for n in range(q):
            if n < remainder:
                lo.append(n * (basesize + 1))
                hi.append(lo[-1] + basesize + 1)
            else:
                lo.append(n*basesize + remainder)
                hi.append(lo[-1] + basesize)

        
        result = seq[lo[p]:hi[p]]
        return result
           
    def joinPartitions(self, listOfPartitions):
        return self.concatenate(listOfPartitions)
                    
    def concatenate(self, listOfPartitions):
        testObject = listOfPartitions[0]
        # First see if we have a known array type
        for m in arrayModules:
            #print m
            if isinstance(testObject, m['type']):
                return m['module'].concatenate(listOfPartitions)
        # Next try for Python sequence types
        if isinstance(testObject, (types.ListType, types.TupleType)):
            return genutil_flatten(listOfPartitions)
        # If we have scalars, just return listOfPartitions
        return listOfPartitions

class RoundRobinMap(Map):
    """Partitions a sequence in a roun robin fashion.
    
    This currently does not work!
    """

    def getPartition(self, seq, p, q):
        return seq[p:len(seq):q]
        #result = []
        #for i in range(p,len(seq),q):
        #    result.append(seq[i])
        #return result

    def joinPartitions(self, listOfPartitions):
        #lengths = [len(x) for x in listOfPartitions]
        #maxPartitionLength = len(listOfPartitions[0])
        #numberOfPartitions = len(listOfPartitions)
        #concat = self.concatenate(listOfPartitions)
        #totalLength = len(concat)
        #result = []
        #for i in range(maxPartitionLength):
        #    result.append(concat[i:totalLength:maxPartitionLength])
        return self.concatenate(listOfPartitions)
        
dists = {'b':Map}

    
    
