import fileinput,os,sys

def oscmd(c):
    os.system(c)

# html manual.
oscmd('sphinx-build -d build/doctrees source build/html')

if sys.platform != 'win32':
    # LaTeX format.
    oscmd('sphinx-build -b latex -d build/doctrees source build/latex')

    # Produce pdf.
    os.chdir('build/latex')

    # Change chapter style to section style: allows chapters to start on the current page.  Works much better for the short chapters we have.
    for line in fileinput.FileInput('manual.cls',inplace=1):
        line=line.replace('py@OldChapter=\chapter','py@OldChapter=\section')
        print line,

    # Copying the makefile produced by sphinx...
    oscmd('pdflatex ipython.tex')
    oscmd('pdflatex ipython.tex')
    oscmd('pdflatex ipython.tex')
    oscmd('makeindex -s python.ist ipython.idx')
    oscmd('makeindex -s python.ist modipython.idx')
    oscmd('pdflatex ipython.tex')
    oscmd('pdflatex ipython.tex')

    os.chdir('../..')
