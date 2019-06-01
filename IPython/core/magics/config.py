"""Implementation of configuration-related magic functions.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import re

# Our own packages
from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class, line_magic
from logging import error

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

reg = re.compile(r'^\w+\.\w+$')
@magics_class
class ConfigMagics(Magics):

    def __init__(self, shell):
        super().__init__(shell)
        self.configurables = []

    @line_magic
    def config(self, s):
        """configure IPython

            %config Class[.trait=value]

        This magic exposes most of the IPython config system. Any
        Configurable class should be able to be configured with the simple
        line::

            %config Class.trait=value

        Where `value` will be resolved in the user's namespace, if it is an
        expression or variable name.

        Examples
        --------

        To see what classes are available for config, pass no arguments::

            In [1]: %config
            Available objects for config:
                TerminalInteractiveShell
                HistoryManager
                PrefilterManager
                AliasManager
                IPCompleter
                DisplayFormatter

        To view what is configurable on a given class, just pass the class
        name::

            In [2]: %config IPCompleter
            IPCompleter options
            -----------------
            IPCompleter.omit__names=<Enum>
                Current: 2
                Choices: (0, 1, 2)
                Instruct the completer to omit private method names
                Specifically, when completing on ``object.<tab>``.
                When 2 [default]: all names that start with '_' will be excluded.
                When 1: all 'magic' names (``__foo__``) will be excluded.
                When 0: nothing will be excluded.
            IPCompleter.merge_completions=<CBool>
                Current: True
                Whether to merge completion results into a single list
                If False, only the completion results from the first non-empty
                completer will be returned.
            IPCompleter.limit_to__all__=<CBool>
                Current: False
                Instruct the completer to use __all__ for the completion
                Specifically, when completing on ``object.<tab>``.
                When True: only those names in obj.__all__ will be included.
                When False [default]: the __all__ attribute is ignored
            IPCompleter.greedy=<CBool>
                Current: False
                Activate greedy completion
                This will enable completion on elements of lists, results of
                function calls, etc., but can be unsafe because the code is
                actually evaluated on TAB.

        but the real use is in setting values::

            In [3]: %config IPCompleter.greedy = True

        and these values are read from the user_ns if they are variables::

            In [4]: feeling_greedy=False

            In [5]: %config IPCompleter.greedy = feeling_greedy

        """
        from traitlets.config.loader import Config
        # some IPython objects are Configurable, but do not yet have
        # any configurable traits.  Exclude them from the effects of
        # this magic, as their presence is just noise:
        configurables = sorted({ c for c in self.shell.configurables
                                     if c.__class__.class_traits(config=True)
                                     }, key=lambda x: x.__class__.__name__)
        classnames = [ c.__class__.__name__ for c in configurables ]

        line = s.strip()
        if not line:
            # print available configurable names
            print("Available objects for config:")
            for name in classnames:
                print("    ", name)
            return
        elif line in classnames:
            # `%config TerminalInteractiveShell` will print trait info for
            # TerminalInteractiveShell
            c = configurables[classnames.index(line)]
            cls = c.__class__
            help = cls.class_get_help(c)
            # strip leading '--' from cl-args:
            help = re.sub(re.compile(r'^--', re.MULTILINE), '', help)
            print(help)
            return
        elif reg.match(line):
            cls, attr = line.split('.')
            return getattr(configurables[classnames.index(cls)],attr)
        elif '=' not in line:
            msg = "Invalid config statement: %r, "\
                  "should be `Class.trait = value`."
            
            ll = line.lower()
            for classname in classnames:
                if ll == classname.lower():
                    msg = msg + '\nDid you mean %s (note the case)?' % classname
                    break

            raise UsageError( msg % line)

        # otherwise, assume we are setting configurables.
        # leave quotes on args when splitting, because we want
        # unquoted args to eval in user_ns
        cfg = Config()
        exec("cfg."+line, locals(), self.shell.user_ns)

        for configurable in configurables:
            try:
                configurable.update_config(cfg)
            except Exception as e:
                error(e)
