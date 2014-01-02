"""ViewWidget class.

Used to display another widget using a different view.
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
from .widget import BaseWidget
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ViewWidget(BaseWidget):
    target_name = Unicode('ViewModel')

    def __init__(self, widget, view):
       self.default_view_name = view
       self.widget = widget
