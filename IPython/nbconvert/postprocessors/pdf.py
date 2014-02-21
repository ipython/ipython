"""
Contains writer for writing nbconvert output to PDF.
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
import sys

from IPython.utils.traitlets import Integer, List, Bool

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class PDFPostProcessor(PostProcessorBase):
    """Writer designed to write to PDF files"""

    latex_count = Integer(3, config=True, help="""
        How many times pdflatex will be called.
        """)

    latex_command = List([u"pdflatex", u"{filename}"], config=True, help="""
        Shell command used to compile PDF.""")

    bib_command = List([u"bibtex", u"{filename}"], config=True, help="""
        Shell command used to run bibtex.""")

    verbose = Bool(False, config=True, help="""
        Whether or not to display the output of the compile call.
        """)

    temp_file_exts = List(['.aux', '.bbl', '.blg', '.idx', '.log', '.out'], 
        config=True, help="""
        Filename extensions of temp files to remove after running.
        """)
    pdf_open = Bool(False, config=True, help="""
        Whether or not to open the pdf after the compile call.
        """)

    def run_command(self, command_list, filename, count, log_function):
        """Run command_list count times.
        
        Parameters
        ----------
        command_list : list
            A list of args to provide to Popen. Each element of this
            list will be interpolated with the filename to convert.
        filename : unicode
            The name of the file to convert.
        count : int
            How many times to run the command.
        
        Returns
        -------
        continue : bool
            A boolean indicating if the command was successful (True)
            or failed (False).
        """
        command = [c.format(filename=filename) for c in command_list]
        #In windows and python 2.x there is a bug in subprocess.Popen and
        # unicode commands are not supported
        if sys.platform == 'win32' and sys.version_info < (3,0):
            #We must use cp1252 encoding for calling subprocess.Popen
            #Note that sys.stdin.encoding and encoding.DEFAULT_ENCODING
            # could be different (cp437 in case of dos console)
            command = [c.encode('cp1252') for c in command]        
        times = 'time' if count == 1 else 'times'
        self.log.info("Running %s %i %s: %s", command_list[0], count, times, command)
        with open(os.devnull, 'rb') as null:
            stdout = subprocess.PIPE if not self.verbose else None
            for index in range(count):
                p = subprocess.Popen(command, stdout=stdout, stdin=null)
                out, err = p.communicate()
                if p.returncode:
                    if self.verbose:
                        # verbose means I didn't capture stdout with PIPE,
                        # so it's already been displayed and `out` is None.
                        out = u''
                    else:
                        out = out.decode('utf-8', 'replace')
                    log_function(command, out)
                    return False # failure
        return True # success

    def run_latex(self, filename):
        """Run pdflatex self.latex_count times."""

        def log_error(command, out):
            self.log.critical(u"%s failed: %s\n%s", command[0], command, out)

        return self.run_command(self.latex_command, filename, 
            self.latex_count, log_error)

    def run_bib(self, filename):
        """Run bibtex self.latex_count times."""
        filename = os.path.splitext(filename)[0]

        def log_error(command, out):
            self.log.warn('%s had problems, most likely because there were no citations',
                command[0])
            self.log.debug(u"%s output: %s\n%s", command[0], command, out)

        return self.run_command(self.bib_command, filename, 1, log_error)

    def clean_temp_files(self, filename):
        """Remove temporary files created by pdflatex/bibtex."""
        self.log.info("Removing temporary LaTeX files")
        filename = os.path.splitext(filename)[0]
        for ext in self.temp_file_exts:
            try:
                os.remove(filename+ext)
            except OSError:
                pass

    def open_pdf(self, filename):
        """Open the pdf in the default viewer."""
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filename))
        elif os.name == 'nt':
            os.startfile(filename)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filename))
        return

    def postprocess(self, filename):
        """Build a PDF by running pdflatex and bibtex"""
        self.log.info("Building PDF")
        cont = self.run_latex(filename)
        if cont:
            cont = self.run_bib(filename)
        else:
            self.clean_temp_files(filename)
            return
        if cont:
            cont = self.run_latex(filename)
        self.clean_temp_files(filename)
        filename = os.path.splitext(filename)[0]
        if os.path.isfile(filename+'.pdf'):
            self.log.info('PDF successfully created')
            if self.pdf_open: 
                self.log.info('Viewer called')
                self.open_pdf(filename+'.pdf')
        return
 
