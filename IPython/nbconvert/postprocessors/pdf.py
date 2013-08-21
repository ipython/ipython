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

from IPython.utils.traitlets import Integer, List, Bool

from .base import PostProcessorBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class PDFPostProcessor(PostProcessorBase):
    """Writer designed to write to PDF files"""

    iteration_count = Integer(3, config=True, help="""
        How many times pdflatex will be called.
        """)

    pdflatex_command = List(["pdflatex", "{filename}"], config=True, help="""
        Shell command used to compile PDF.""")

    bibtex_command = List(["bibtex", "{filename}"], config=True, help="""
        Shell command used to run bibtex.""")

    verbose = Bool(False, config=True, help="""
        Whether or not to display the output of the compile call.
        """)

    temp_file_exts = List(['.aux', '.bbl', '.blg', '.idx', '.log', '.out'], 
        config=True, help="""
        Filename extensions of temp files to remove after running
        """)

    def run_command(self, command_list, filename, count, log_function):
        """Run pdflatex or bibtext count times.
        
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

    def run_pdflatex(self, filename):
        """Run pdflatex self.iteration_count times."""

        def log_error(command, out):
            self.log.critical(u"pdflatex failed: %s\n%s", command, out)

        return self.run_command(self.pdflatex_command, filename, 
            self.iteration_count, log_error)

    def run_bibtex(self, filename):
        """Run bibtex self.iteration_count times."""
        filename = filename.rstrip('.tex')
        
        def log_error(command, out):
            self.log.warn('bibtex had problems, most likely because there were no citations')
            self.log.debug(u"bibtex output: %s\n%s", command, out)

        return self.run_command(self.bibtex_command, filename, 1, log_error)

    def clean_temp_files(self, filename):
        """Remove temporary files created by pdflatex/bibtext."""
        self.log.info("Removing temporary LaTeX files")
        filename = filename.strip('.tex')
        for ext in self.temp_file_exts:
            try:
                os.remove(filename+ext)
            except OSError:
                pass
        
    def postprocess(self, filename):
        """Build a PDF by running pdflatex and bibtex"""
        self.log.info("Building PDF")
        cont = self.run_pdflatex(filename)
        if cont:
            cont = self.run_bibtex(filename)
        else:
            self.clean_temp_files(filename)
            return
        if cont:
            cont = self.run_pdflatex(filename)
        self.clean_temp_files(filename)
        if os.path.isfile(filename.rstrip('.tex')+'.pdf'):
            self.log.info('PDF successfully created')
        return

