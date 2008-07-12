# encoding: utf-8

""" Manage the input and output history of the interpreter and the
frontend.

There are 2 different history objects, one that lives in the interpreter,
and one that lives in the frontend. They are synced with a diff at each
execution of a command, as the interpreter history is a real stack, its
existing entries are not mutable.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from copy import copy

# Local imports.
from util import InputList


##############################################################################
class History(object):
    """ An object managing the input and output history.
    """

    def __init__(self, input_cache=None, output_cache=None):

        # Stuff that IPython adds to the namespace.
        self.namespace_additions = dict(
            _ = None,
            __ = None,
            ___ = None,
        )

        # A list to store input commands.
        if input_cache is None:
            input_cache =InputList([])
        self.input_cache = input_cache

        # A dictionary to store trapped output.
        if output_cache is None:
            output_cache = {}
        self.output_cache = output_cache

    def get_history_item(self, index):
        """ Returns the history string at index, where index is the
        distance from the end (positive). 
        """
        if index>=0 and index<len(self.input_cache):
            return self.input_cache[index]


##############################################################################
class InterpreterHistory(History):
    """ An object managing the input and output history at the interpreter
    level.
    """

    def setup_namespace(self, namespace):
        """ Add the input and output caches into the interpreter's namespace
        with IPython-conventional names.

        Parameters
        ----------
        namespace : dict
        """

        namespace['In'] = self.input_cache
        namespace['_ih'] = self.input_cache
        namespace['Out'] = self.output_cache
        namespace['_oh'] = self.output_cache

    def update_history(self, interpreter, python):
        """ Update the history objects that this object maintains and the
        interpreter's namespace.

        Parameters
        ----------
        interpreter : Interpreter
        python : str
            The real Python code that was translated and actually executed.
        """

        number = interpreter.current_cell_number

        new_obj = interpreter.display_trap.obj
        if new_obj is not None:
            self.namespace_additions['___'] = self.namespace_additions['__']
            self.namespace_additions['__'] = self.namespace_additions['_']
            self.namespace_additions['_'] = new_obj
            self.output_cache[number] = new_obj

        interpreter.user_ns.update(self.namespace_additions)
        self.input_cache.add(number, python)


    def get_history_item(self, index):
        """ Returns the history string at index, where index is the
        distance from the end (positive). 
        """
        if index>0 and index<(len(self.input_cache)-1):
            return self.input_cache[-index]

    def get_input_cache(self):
        return copy(self.input_cache)

    def get_input_after(self, index):
        """ Returns the list of the commands entered after index.
        """
        # We need to call directly list.__getslice__, because this object
        # is not a real list.
        return list.__getslice__(self.input_cache, index,
                                                len(self.input_cache))


##############################################################################
class FrontEndHistory(History):
    """ An object managing the input and output history at the frontend.
        It is used as a local cache to reduce network latency problems
        and multiple users editing the same thing.
    """

    def add_items(self, item_list):
        """ Adds the given command list to the stack of executed
            commands.
        """
        self.input_cache.extend(item_list)
