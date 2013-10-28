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
from IPython.utils.traitlets import Unicode, Dict

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class MulticontainerWidget(Widget):
    target_name = Unicode('MulticontainerWidgetModel')
    default_view_name = Unicode('TabView')

    # Keys
    _keys = ['_titles']
    _titles = Dict(help="Titles of the pages")

    # Public methods
    def set_title(self, index, title):
        """Sets the title of a container pages

        Parameters
        ----------
        index : int
            Index of the container page
        title : unicode
            New title"""
        self._titles[index] = title
        self.send_state('_titles')


    def get_title(self, index):
        """Gets the title of a container pages

        Parameters
        ----------
        index : int
            Index of the container page"""
        if index in self._titles:
            return self._titles[index]
        else:
            return None
