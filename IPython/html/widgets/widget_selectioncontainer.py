"""SelectionContainerWidget class.  

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
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Dict, Int, List, Instance

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class AccordionWidget(DOMWidget):
    view_name = Unicode('AccordionView', sync=True)

    # Keys
    _titles = Dict(help="Titles of the pages", sync=True)
    selected_index = Int(0, sync=True)

    children = List(Instance(DOMWidget))

    # Public methods
    def set_title(self, index, title):
        """Sets the title of a container page

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


class TabWidget(AccordionWidget):
    view_name = Unicode('TabView', sync=True)
