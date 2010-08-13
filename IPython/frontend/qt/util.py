""" Defines miscellaneous Qt-related helper classes and functions.
"""

# System library imports.
from PyQt4 import QtCore

# IPython imports.
from IPython.utils.traitlets import HasTraits

#-----------------------------------------------------------------------------
# Metaclasses
#-----------------------------------------------------------------------------

MetaHasTraits = type(HasTraits)
MetaQObject = type(QtCore.QObject)

# You can switch the order of the parents here and it doesn't seem to matter.
class MetaQObjectHasTraits(MetaQObject, MetaHasTraits):
    """ A metaclass that inherits from the metaclasses of both HasTraits and
        QObject. 

        Using this metaclass allows a class to inherit from both HasTraits and
        QObject. See QtKernelManager for an example.
    """
    pass
