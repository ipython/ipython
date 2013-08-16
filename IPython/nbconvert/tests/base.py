"""
Contains base test class for nbconvert
"""
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import glob
import shutil

import IPython
from IPython.utils.tempdir import TemporaryWorkingDirectory
from IPython.utils.process import get_output_error_code
from IPython.testing.tools import get_ipython_cmd
from IPython.testing.ipunittest import ParametricTestCase

# a trailing space allows for simpler concatenation with the other arguments
ipy_cmd = get_ipython_cmd(as_string=True) + " "

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class TestsBase(ParametricTestCase):
    """Base tests class.  Contains useful fuzzy comparison and nbconvert
    functions."""


    def fuzzy_compare(self, a, b, newlines_are_spaces=True, tabs_are_spaces=True, 
                      fuzzy_spacing=True, ignore_spaces=False, 
                      ignore_newlines=False, case_sensitive=False, leave_padding=False):
        """
        Performs a fuzzy comparison of two strings.  A fuzzy comparison is a
        comparison that ignores insignificant differences in the two comparands.
        The significance of certain differences can be specified via the keyword
        parameters of this method.
        """

        if not leave_padding:
            a = a.strip()
            b = b.strip()

        if ignore_newlines:
            a = a.replace('\n', '')
            b = b.replace('\n', '')

        if newlines_are_spaces:
            a = a.replace('\n', ' ')
            b = b.replace('\n', ' ')

        if tabs_are_spaces:
            a = a.replace('\t', ' ')
            b = b.replace('\t', ' ')

        if ignore_spaces:
            a = a.replace(' ', '')
            b = b.replace(' ', '')

        if fuzzy_spacing:
            a = self.recursive_replace(a, '  ', ' ')
            b = self.recursive_replace(b, '  ', ' ')

        if not case_sensitive:
            a = a.lower()
            b = b.lower()

        self.assertEqual(a, b)


    def recursive_replace(self, text, search, replacement):
        """
        Performs a recursive replacement operation.  Replaces all instances
        of a search string in a text string with a replacement string until
        the search string no longer exists.  Recursion is needed because the
        replacement string may generate additional search strings.

        For example:
           Replace "ii" with "i" in the string "Hiiii" yields "Hii"
           Another replacement yields "Hi" (the desired output)

        Parameters:
        -----------
        text : string
            Text to replace in.
        search : string
            String to search for within "text"
        replacement : string
            String to replace "search" with
        """
        while search in text:
            text = text.replace(search, replacement)
        return text

    def create_temp_cwd(self, copy_filenames=None):
        temp_dir = TemporaryWorkingDirectory()

        #Copy the files if requested.
        if copy_filenames is not None:
            self.copy_files_to(copy_filenames)

        #Return directory handler
        return temp_dir


    def copy_files_to(self, copy_filenames, dest='.'):
        "Copy test files into the destination directory"
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files_path = self._get_files_path()
        for pattern in copy_filenames:
            for match in glob.glob(os.path.join(files_path, pattern)):
                shutil.copyfile(match, os.path.join(dest, os.path.basename(match)))


    def _get_files_path(self):

        #Get the relative path to this module in the IPython directory.
        names = self.__module__.split('.')[1:-1]
        names.append('files')
        
        #Build a path using the IPython directory and the relative path we just
        #found.
        path = IPython.__path__[0]
        for name in names:
            path = os.path.join(path, name)
        return path


    def call(self, parameters, ignore_return_code=False):
        """
        Execute a, IPython shell command, listening for both Errors and non-zero
        return codes.

        PARAMETERS:
        -----------
        parameters : str
            List of parameters to pass to IPython.
        ignore_return_code : optional bool (default False)
            Throw an OSError if the return code
        """

        stdout, stderr, retcode = get_output_error_code(ipy_cmd + parameters)
        if not (retcode == 0 or ignore_return_code):
            raise OSError(stderr)
        return stdout, stderr
