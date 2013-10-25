"""MulticontainerWidget class.  

Represents a multipage container that can be used to group other widgets into
pages.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from widget import Widget
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class MulticontainerWidget(Widget):
    target_name = Unicode('MulticontainerWidgetModel')
    default_view_name = Unicode('AccordionView')
