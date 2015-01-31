"""Export to PDF via latex"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import subprocess
import os
import sys

from IPython.utils.process import find_cmd
from IPython.utils.traitlets import Integer, List, Bool, Instance
from IPython.utils.tempdir import TemporaryWorkingDirectory
from .latex import LatexExporter


class PDFExporter(LatexExporter):
    """Writer designed to write to PDF files"""

    latex_count = Integer(3, config=True,
        help="How many times latex will be called."
    )

    latex_command = List([u"pdflatex", u"{filename}"], config=True, 
        help="Shell command used to compile latex."
    )

    bib_command = List([u"bibtex", u"{filename}"], config=True,
        help="Shell command used to run bibtex."
    )

    verbose = Bool(False, config=True,
        help="Whether to display the output of latex commands."
    )

    temp_file_exts = List(['.aux', '.bbl', '.blg', '.idx', '.log', '.out'], config=True,
        help="File extensions of temp files to remove after running."
    )
    
    writer = Instance("IPython.nbconvert.writers.FilesWriter", args=())

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
        success : bool
            A boolean indicating if the command was successful (True)
            or failed (False).
        """
        command = [c.format(filename=filename) for c in command_list]

        # On windows with python 2.x there is a bug in subprocess.Popen and
        # unicode commands are not supported
        if sys.platform == 'win32' and sys.version_info < (3,0):
            #We must use cp1252 encoding for calling subprocess.Popen
            #Note that sys.stdin.encoding and encoding.DEFAULT_ENCODING
            # could be different (cp437 in case of dos console)
            command = [c.encode('cp1252') for c in command]        

        # This will throw a clearer error if the command is not found
        find_cmd(command_list[0])
        
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

    def from_notebook_node(self, nb, resources=None, **kw):
        latex, resources = super(PDFExporter, self).from_notebook_node(
            nb, resources=resources, **kw
        )
        with TemporaryWorkingDirectory() as td:
            notebook_name = "notebook"
            tex_file = self.writer.write(latex, resources, notebook_name=notebook_name)
            self.log.info("Building PDF")
            rc = self.run_latex(tex_file)
            if not rc:
                rc = self.run_bib(tex_file)
            if not rc:
                rc = self.run_latex(tex_file)
            
            pdf_file = notebook_name + '.pdf'
            if not os.path.isfile(pdf_file):
                raise RuntimeError("PDF creating failed")
            self.log.info('PDF successfully created')
            with open(pdf_file, 'rb') as f:
                pdf_data = f.read()
        
        # convert output extension to pdf
        # the writer above required it to be tex
        resources['output_extension'] = '.pdf'
        
        return pdf_data, resources
    
