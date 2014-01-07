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
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Bool, List, Instance

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ContainerWidget(DOMWidget):
    target_name = Unicode('ContainerWidgetModel')
    default_view_name = Unicode('ContainerView')

    # Keys, all private and managed by helper methods.  Flexible box model
    # classes...
    keys = ['_vbox', '_hbox', '_align_start', '_align_end', '_align_center',
            '_pack_start', '_pack_end', '_pack_center', '_flex0', '_flex1', 
            '_flex2', 'description', 'button_text',
            'children'] + DOMWidget.keys
    children = List(Instance(DOMWidget))
    
    description = Unicode()
    button_text = Unicode()
    _hbox = Bool(False)
    _vbox = Bool(False)
    _align_start = Bool(False)
    _align_end = Bool(False)
    _align_center = Bool(False)
    _pack_start = Bool(False)
    _pack_end = Bool(False)
    _pack_center = Bool(False)
    _flex0 = Bool(False)
    _flex1 = Bool(False)
    _flex2 = Bool(False)
    
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

            
    def flex0(self, enabled=True):
        """Put this container in flex0 mode.  Automatically disables conflicting
        flex modes.  See the widget tutorial part 5 example notebook for more
        information.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the flex0 attribute of the container, defaults to 
            True."""
        self._flex0 = enabled
        if enabled:
            self._flex1 = False
            self._flex2 = False
            
    def flex1(self, enabled=True):
        """Put this container in flex1 mode.  Automatically disables conflicting
        flex modes.  See the widget tutorial part 5 example notebook for more
        information.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the flex1 attribute of the container, defaults to 
            True."""
        self._flex1 = enabled
        if enabled:
            self._flex0 = False
            self._flex2 = False
            
    def flex2(self, enabled=True):
        """Put this container in flex2 mode.  Automatically disables conflicting
        flex modes.  See the widget tutorial part 5 example notebook for more
        information.

        Parameters
        ----------
        enabled: bool (optional)
            Enabled or disable the flex2 attribute of the container, defaults to 
            True."""
        self._flex2 = enabled
        if enabled:
            self._flex0 = False
            self._flex1 = False
