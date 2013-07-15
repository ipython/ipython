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

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestsBase(object):
    """Base tests class.  Contains usefull fuzzy comparison and nbconvert
    functions."""


    def fuzzy_compare(self, a, b, newlines_are_spaces=True, tabs_are_spaces=True, 
                      fuzzy_spacing=True, ignore_spaces=False, 
                      ignore_newlines=False, ignore_case=True):
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

        if ignore_case:
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
     