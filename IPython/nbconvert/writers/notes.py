"""
Contains writer for writing speaker notes plugin for reveal slides.
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
import urllib2
import codecs

from .files import FilesWriter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class NotesWriter(FilesWriter):
    """Build the reveal speaker notes plugin infrastructure 
       to support the speaker notes functionality."""


    def write_notes(self):
            """Writes the necessary html and js files."""

            html_infile = 'http://cdn.jsdelivr.net/reveal.js/2.4.0/plugin/notes/notes.html'
            html_outfile = "notes.html"    
            self.write_helper(html_infile, html_outfile)
            
            js_infile = 'http://cdn.jsdelivr.net/reveal.js/2.4.0/plugin/notes/notes.js'
            js_outfile = "notes.js"
            self.write_helper(js_infile, js_outfile)
            

    def write_helper(self, infile, outfile):
            """Helper function to write the content of a url to a file."""
            
            notes_path = "reveal.js/plugin/notes"
            dir_dest = os.path.join(self.build_directory, notes_path)
            if not os.path.isdir(dir_dest):
                os.makedirs(dir_dest)
            
            file_dest = os.path.join(dir_dest, outfile)
            
            with codecs.open(file_dest, 'w', 'utf-8') as f:
                f.write(urllib2.urlopen(infile).read())