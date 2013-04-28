"""Filter used to select the first prefered output format available.

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
class DataTypeFilter(GlobalConfigurable):
    """ Returns the prefered display format """

    def __init__(self, config=None, **kw):
        super(FilterDataType, self).__init__(config=config, **kw)

    def __call__(self, output):
        """ Return the first available format in the priority """

        for fmt in self.display_data_priority:
            if fmt in output:
                return [fmt]
        return []