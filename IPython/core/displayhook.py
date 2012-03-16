# -*- coding: utf-8 -*-
"""Displayhook for IPython.

This defines a callable class that IPython uses for `sys.displayhook`.

Authors:

* Fernando Perez
* Brian Granger
* Robert Kern
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2011 The IPython Development Team
#       Copyright (C) 2001-2007 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__

from IPython.config.configurable import Configurable
from IPython.utils import io
from IPython.utils.traitlets import Instance, List
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Main displayhook class
#-----------------------------------------------------------------------------

# TODO: Move the various attributes (cache_size, [others now moved]). Some
# of these are also attributes of InteractiveShell. They should be on ONE object
# only and the other objects should ask that one object for their values.

class DisplayHook(Configurable):
    """The custom IPython displayhook to replace sys.displayhook.

    This class does many things, but the basic idea is that it is a callable
    that gets called anytime user code returns a value.
    """

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def __init__(self, shell=None, cache_size=1000, config=None):
        super(DisplayHook, self).__init__(shell=shell, config=config)

        cache_size_min = 3
        if cache_size <= 0:
            self.do_full_cache = 0
            cache_size = 0
        elif cache_size < cache_size_min:
            self.do_full_cache = 0
            cache_size = 0
            warn('caching was disabled (min value for cache size is %s).' %
                 cache_size_min,level=3)
        else:
            self.do_full_cache = 1

        self.cache_size = cache_size

        # we need a reference to the user-level namespace
        self.shell = shell
        
        self._,self.__,self.___ = '','',''

        # these are deliberately global:
        to_user_ns = {'_':self._,'__':self.__,'___':self.___}
        self.shell.user_ns.update(to_user_ns)

    @property
    def prompt_count(self):
        return self.shell.execution_count

    #-------------------------------------------------------------------------
    # Methods used in __call__. Override these methods to modify the behavior
    # of the displayhook.
    #-------------------------------------------------------------------------

    def check_for_underscore(self):
        """Check if the user has set the '_' variable by hand."""
        # If something injected a '_' variable in __builtin__, delete
        # ipython's automatic one so we don't clobber that.  gettext() in
        # particular uses _, so we need to stay away from it.
        if '_' in __builtin__.__dict__:
            try:
                del self.shell.user_ns['_']
            except KeyError:
                pass

    def quiet(self):
        """Should we silence the display hook because of ';'?"""
        # do not print output if input ends in ';'
        try:
            cell = self.shell.history_manager.input_hist_parsed[self.prompt_count]
            if cell.rstrip().endswith(';'):
                return True
        except IndexError:
            # some uses of ipshellembed may fail here
            pass
        return False

    def start_displayhook(self):
        """Start the displayhook, initializing resources."""
        pass

    def write_output_prompt(self):
        """Write the output prompt.

        The default implementation simply writes the prompt to
        ``io.stdout``.
        """
        # Use write, not print which adds an extra space.
        io.stdout.write(self.shell.separate_out)
        outprompt = self.shell.prompt_manager.render('out')
        if self.do_full_cache:
            io.stdout.write(outprompt)

    def compute_format_data(self, result):
        """Compute format data of the object to be displayed.

        The format data is a generalization of the :func:`repr` of an object.
        In the default implementation the format data is a :class:`dict` of
        key value pair where the keys are valid MIME types and the values
        are JSON'able data structure containing the raw data for that MIME
        type. It is up to frontends to determine pick a MIME to to use and
        display that data in an appropriate manner.

        This method only computes the format data for the object and should
        NOT actually print or write that to a stream.

        Parameters
        ----------
        result : object
            The Python object passed to the display hook, whose format will be
            computed.

        Returns
        -------
        format_data : dict
            A :class:`dict` whose keys are valid MIME types and values are
            JSON'able raw data for that MIME type. It is recommended that
            all return values of this should always include the "text/plain"
            MIME type representation of the object.
        """
        return self.shell.display_formatter.format(result)

    def write_format_data(self, format_dict):
        """Write the format data dict to the frontend.

        This default version of this method simply writes the plain text
        representation of the object to ``io.stdout``. Subclasses should
        override this method to send the entire `format_dict` to the
        frontends.

        Parameters
        ----------
        format_dict : dict
            The format dict for the object passed to `sys.displayhook`.
        """
        # We want to print because we want to always make sure we have a
        # newline, even if all the prompt separators are ''. This is the
        # standard IPython behavior.
        result_repr = format_dict['text/plain']
        if '\n' in result_repr:
            # So that multi-line strings line up with the left column of
            # the screen, instead of having the output prompt mess up
            # their first line.
            # We use the prompt template instead of the expanded prompt
            # because the expansion may add ANSI escapes that will interfere
            # with our ability to determine whether or not we should add
            # a newline.
            prompt_template = self.shell.prompt_manager.out_template
            if prompt_template and not prompt_template.endswith('\n'):
                # But avoid extraneous empty lines.
                result_repr = '\n' + result_repr

        print >>io.stdout, result_repr

    def update_user_ns(self, result):
        """Update user_ns with various things like _, __, _1, etc."""

        # Avoid recursive reference when displaying _oh/Out
        if result is not self.shell.user_ns['_oh']:
            if len(self.shell.user_ns['_oh']) >= self.cache_size and self.do_full_cache:
                warn('Output cache limit (currently '+
                      `self.cache_size`+' entries) hit.\n'
                     'Flushing cache and resetting history counter...\n'
                     'The only history variables available will be _,__,___ and _1\n'
                     'with the current result.')

                self.flush()
            # Don't overwrite '_' and friends if '_' is in __builtin__ (otherwise
            # we cause buggy behavior for things like gettext).

            if '_' not in __builtin__.__dict__:
                self.___ = self.__
                self.__ = self._
                self._ = result
                self.shell.push({'_':self._,
                                 '__':self.__,
                                '___':self.___}, interactive=False)

            # hackish access to top-level  namespace to create _1,_2... dynamically
            to_main = {}
            if self.do_full_cache:
                new_result = '_'+`self.prompt_count`
                to_main[new_result] = result
                self.shell.push(to_main, interactive=False)
                self.shell.user_ns['_oh'][self.prompt_count] = result

    def log_output(self, format_dict):
        """Log the output."""
        if self.shell.logger.log_output:
            self.shell.logger.log_write(format_dict['text/plain'], 'output')
        self.shell.history_manager.output_hist_reprs[self.prompt_count] = \
                                                    format_dict['text/plain']

    def finish_displayhook(self):
        """Finish up all displayhook activities."""
        io.stdout.write(self.shell.separate_out2)
        io.stdout.flush()

    def __call__(self, result=None):
        """Printing with history cache management.

        This is invoked everytime the interpreter needs to print, and is
        activated by setting the variable sys.displayhook to it.
        """
        self.check_for_underscore()
        if result is not None and not self.quiet():
            self.start_displayhook()
            self.write_output_prompt()
            format_dict = self.compute_format_data(result)
            self.write_format_data(format_dict)
            self.update_user_ns(result)
            self.log_output(format_dict)
            self.finish_displayhook()

    def flush(self):
        if not self.do_full_cache:
            raise ValueError,"You shouldn't have reached the cache flush "\
                  "if full caching is not enabled!"
        # delete auto-generated vars from global namespace

        for n in range(1,self.prompt_count + 1):
            key = '_'+`n`
            try:
                del self.shell.user_ns[key]
            except: pass
        # In some embedded circumstances, the user_ns doesn't have the
        # '_oh' key set up.
        oh = self.shell.user_ns.get('_oh', None)
        if oh is not None:
            oh.clear()

        # Release our own references to objects:
        self._, self.__, self.___ = '', '', ''

        if '_' not in __builtin__.__dict__:
            self.shell.user_ns.update({'_':None,'__':None, '___':None})
        import gc
        # TODO: Is this really needed?
        gc.collect()

