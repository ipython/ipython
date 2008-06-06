# encoding: utf-8

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

import os
import __builtin__

# Local imports.
from util import Bunch


# fixme: RTK thinks magics should be implemented as separate classes rather than
# methods on a single class. This would give us the ability to plug new magics
# in and configure them separately.

class Magic(object):
    """ An object that maintains magic functions.
    """

    def __init__(self, interpreter, config=None):
        # A reference to the interpreter.
        self.interpreter = interpreter

        # A reference to the configuration object.
        if config is None:
            # fixme: we need a better place to store this information.
            config = Bunch(ESC_MAGIC='%')
        self.config = config

    def has_magic(self, name):
        """ Return True if this object provides a given magic.

        Parameters
        ----------
        name : str
        """

        return hasattr(self, 'magic_' + name)

    def object_find(self, name):
        """ Find an object in the available namespaces.

        fixme: this should probably be moved elsewhere. The interpreter?
        """

        name = name.strip()

        # Namespaces to search.
        # fixme: implement internal and alias namespaces.
        user_ns = self.interpreter.user_ns
        internal_ns = {}
        builtin_ns = __builtin__.__dict__
        alias_ns = {}

        # Order the namespaces.
        namespaces = [
            ('Interactive', user_ns),
            ('IPython internal', internal_ns),
            ('Python builtin', builtin_ns),
            ('Alias', alias_ns),
        ]

        # Initialize all results.
        found = False
        obj = None
        space = None
        ds = None
        ismagic = False
        isalias = False

        # Look for the given name by splitting it in parts.  If the head is
        # found, then we look for all the remaining parts as members, and only
        # declare success if we can find them all.
        parts = name.split('.')
        head, rest = parts[0], parts[1:]
        for nsname, ns in namespaces:
            try:
                obj = ns[head]
            except KeyError:
                continue
            else:
                for part in rest:
                    try:
                        obj = getattr(obj, part)
                    except:
                        # Blanket except b/c some badly implemented objects
                        # allow __getattr__ to raise exceptions other than
                        # AttributeError, which then crashes us.
                        break
                else:
                    # If we finish the for loop (no break), we got all members
                    found = True
                    space = nsname
                    isalias = (ns == alias_ns)
                    break  # namespace loop

        # Try to see if it is a magic.
        if not found:
            if name.startswith(self.config.ESC_MAGIC):
                name = name[1:]
            obj = getattr(self, 'magic_' + name, None)
            if obj is not None:
                found = True
                space = 'IPython internal'
                ismagic = True

        # Last try: special-case some literals like '', [], {}, etc:
        if not found and head in ["''", '""', '[]', '{}', '()']:
            obj = eval(head)
            found = True
            space = 'Interactive'

        return dict(
            found=found,
            obj=obj,
            namespace=space,
            ismagic=ismagic,
            isalias=isalias,
        )
            
                    



    def magic_pwd(self, parameter_s=''):
        """ Return the current working directory path.
        """
        return os.getcwd()

    def magic_env(self, parameter_s=''):
        """ List environment variables.
        """
        
        return os.environ.data


