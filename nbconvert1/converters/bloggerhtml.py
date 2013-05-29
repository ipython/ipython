"""Notebook export in Blogger-aware HTML.

This file contains `ConverterBloggerHTML`, a subclass of `ConverterHTML` that
provides output suitable for easy pasting into a blog hosted on the Blogger
platform. See the class docstring for more information.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib imports
import io

# Our own imports
from .html import ConverterHTML


#-----------------------------------------------------------------------------
# Classes declarations
#-----------------------------------------------------------------------------

class ConverterBloggerHTML(ConverterHTML):
    """Convert a notebook to html suitable for easy pasting into Blogger.

    It generates an html file that has *only* the pure HTML contents, and a
    separate file with `_header` appended to the name with all header contents.
    Typically, the header file only needs to be used once when setting up a
    blog, as the CSS for all posts is stored in a single location in Blogger.
    """

    def optional_header(self):
        with io.open(self.outbase + '_header.html', 'w',
                     encoding=self.default_encoding) as f:
            f.write('\n'.join(self.header_body()))
        return []

    def optional_footer(self):
        return []
