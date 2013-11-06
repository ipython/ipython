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
from .widget import Widget
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ContainerWidget(Widget):
    target_name = Unicode('ContainerWidgetModel')
    default_view_name = Unicode('ContainerView')

    # Keys, all private and managed by helper methods.  Flexible box model
    # classes...
    _keys = ['_vbox', '_hbox', '_align_start', '_align_end', '_align_center',
            '_pack_start', '_pack_end', '_pack_center']
    _hbox = Bool(False)
    _vbox = Bool(False)
    _align_start = Bool(False)
    _align_end = Bool(False)
    _align_center = Bool(False)
    _pack_start = Bool(False)
    _pack_end = Bool(False)
    _pack_center = Bool(False)
    
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
            
    def align_start(self, enabled=True):
        """Make the contents of this container align to the start of the axis.  
        Automatically disables conflicting alignments.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the start alignment of the container, defaults to 
            True."""
        self._align_start = enabled
        if enabled:
            self._align_end = False
            self._align_center = False
            
    def align_end(self, enabled=True):
        """Make the contents of this container align to the end of the axis.  
        Automatically disables conflicting alignments.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the end alignment of the container, defaults to 
            True."""
        self._align_end = enabled
        if enabled:
            self._align_start = False
            self._align_center = False
            
    def align_center(self, enabled=True):
        """Make the contents of this container align to the center of the axis.  
        Automatically disables conflicting alignments.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the center alignment of the container, defaults to 
            True."""
        self._align_center = enabled
        if enabled:
            self._align_start = False
            self._align_end = False

            
    def pack_start(self, enabled=True):
        """Make the contents of this container pack to the start of the axis.  
        Automatically disables conflicting packings.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the start packing of the container, defaults to 
            True."""
        self._pack_start = enabled
        if enabled:
            self._pack_end = False
            self._pack_center = False
            
    def pack_end(self, enabled=True):
        """Make the contents of this container pack to the end of the axis.  
        Automatically disables conflicting packings.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the end packing of the container, defaults to 
            True."""
        self._pack_end = enabled
        if enabled:
            self._pack_start = False
            self._pack_center = False
            
    def pack_center(self, enabled=True):
        """Make the contents of this container pack to the center of the axis.  
        Automatically disables conflicting packings.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the center packing of the container, defaults to 
            True."""
        self._pack_center = enabled
        if enabled:
            self._pack_start = False
            self._pack_end = False
