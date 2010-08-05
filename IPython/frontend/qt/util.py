""" Defines miscellaneous Qt-related helper classes and functions.
"""

# System library imports.
from PyQt4 import QtCore

# IPython imports.
from IPython.utils.traitlets import HasTraits


MetaHasTraits = type(HasTraits)
MetaQObject = type(QtCore.QObject)

# You can switch the order of the parents here.
class MetaQObjectHasTraits(MetaQObject, MetaHasTraits):
    """ A metaclass that inherits from the metaclasses of both HasTraits and
        QObject. 

        Using this metaclass allows a class to inherit from both HasTraits and
        QObject. See QtKernelManager for an example.
    """
    # pass
    # ???You can get rid of this, but only if the order above is MetaQObject, MetaHasTraits
    # def __init__(cls, name, bases, dct):
    #     MetaQObject.__init__(cls, name, bases, dct)
    #     MetaHasTraits.__init__(cls, name, bases, dct)

