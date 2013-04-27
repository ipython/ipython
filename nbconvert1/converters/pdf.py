from .latex import ConverterLaTeX
import subprocess

class ConverterLaTeXToPDF(ConverterLaTeX):
    def render(self):
        super(ConverterLaTeXToPDF, self).render()
        subprocess.check_call(['pdflatex', self.outbase + '.tex'])
