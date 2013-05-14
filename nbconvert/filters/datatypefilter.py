"""Filter used to select the first preferred output format available.

The filter contained in the file allows the converter templates to select
the output format that is most valuable to the active export format.  The
value of the different formats is set via 
GlobalConfigurable.display_data_priority
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
class DataTypeFilter(object):
    """ Returns the preferred display format """

    display_data_priority = None

    def __init__(self, display_data_priority):
        
        #Make sure that the display data priority variably is not None.
        if display_data_priority is None:
            raise TypeError
        else:
            self.display_data_priority = display_data_priority
        

    def __call__(self, output):
        """ Return the first available format in the priority """

        for fmt in self.display_data_priority:
            if fmt in output:
                return [fmt]
        return []