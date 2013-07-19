#!/usr/bin/env python
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

import subprocess
import os
import glob
import shutil
import sys

import IPython
from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TemporaryWorkingDirectory(TemporaryDirectory):
    """
    Creates a temporary directory and sets the cwd to that directory.
    Automatically reverts to previous cwd upon cleanup.
    Usage example:

        with TemporaryWorakingDirectory() as tmpdir:
            ...
    """

    def __init__(self, **kw):
        """
        Constructor
        """
        super(TemporaryWorkingDirectory, self).__init__(**kw)

        #Change cwd to new temp dir.  Remember old cwd.
        self.old_wd = os.getcwd()
        os.chdir(self.name)


    def cleanup(self):
        """
        Destructor
        """

        #Revert to old cwd.
        os.chdir(self.old_wd)

        #Cleanup
        super(TemporaryWorkingDirectory, self).cleanup()


class TestsBase(object):
    """Base tests class.  Contains usefull fuzzy comparison and nbconvert
    functions."""


    def fuzzy_compare(self, a, b, newlines_are_spaces=True, tabs_are_spaces=True, 
                      fuzzy_spacing=True, ignore_spaces=False, 
                      ignore_newlines=False, case_sensitive=False):
        """
        Performs a fuzzy comparison of two strings.  A fuzzy comparison is a
        comparison that ignores insignificant differences in the two comparands.
        The significance of certain differences can be specified via the keyword
        parameters of this method.
        """

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

        if ignore_newlines:
            a = a.replace('\n', '')
            b = b.replace('\n', '')

        if not case_sensitive:
            a = a.lower()
            b = b.lower()

        return a == b


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
        if not copy_filenames is None:
            self.copy_files_to(copy_filenames)

        #Return directory handler
        return temp_dir


    def copy_files_to(self, copy_filenames=None, destination=None):
        
        #Copy test files into the destination directory.
        if copy_filenames:
            for pattern in copy_filenames:
                for match in glob.glob(os.path.join(self._get_files_path(), pattern)):
                    if destination is None:
                        shutil.copyfile(match, os.path.basename(match))
                    else:
                        if not os.path.isdir(destination):
                            os.makedirs(destination)
                        shutil.copyfile(match, os.path.join(destination, os.path.basename(match)))


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


    def call(self, parameters):
        output = subprocess.Popen(parameters, stdout=subprocess.PIPE).communicate()[0]
        
        #Convert the output to a string if running Python3
        if py3compat.PY3:
            return output.decode('utf-8')
        else:
            return output
     