"""ContainerWidget class.  

Represents a container that can be used to group other widgets.
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
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ContainerWidget(Widget):
    target_name = Unicode('ContainerWidgetModel')
    default_view_name = Unicode('ContainerView')

    # Keys, all private and managed by helper methods.  Flexible box model
    # classes...
    _keys = ['_vbox', '_hbox', '_start', '_end', '_center']
    _hbox = Bool(False)
    _vbox = Bool(False)
    _start = Bool(False)
    _end = Bool(False)
    _center = Bool(False)
    
    def hbox(self, enabled=True):
        """Make this container an hbox.  Automatically disables conflicting
        features.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the hbox feature of the container, defaults to 
            True."""
        self._hbox = enabled
        if enabled:
            self._vbox = False
    
    def vbox(self, enabled=True):
        """Make this container an vbox.  Automatically disables conflicting
        features.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the vbox feature of the container, defaults to 
            True."""
        self._vbox = enabled
        if enabled:
            self._hbox = False
            
    def start(self, enabled=True):
        """Make the contents of this container align to the start of the axis.  
        Automatically disables conflicting alignments.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the start alignment of the container, defaults to 
            True."""
        self._start = enabled
        if enabled:
            self._end = False
            self._center = False
            
    def end(self, enabled=True):
        """Make the contents of this container align to the end of the axis.  
        Automatically disables conflicting alignments.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the end alignment of the container, defaults to 
            True."""
        self._end = enabled
        if enabled:
            self._start = False
            self._center = False
            
    def center(self, enabled=True):
        """Make the contents of this container align to the center of the axis.  
        Automatically disables conflicting alignments.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the center alignment of the container, defaults to 
            True."""
        self._center = enabled
        if enabled:
            self._start = False
            self._end = False
