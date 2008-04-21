import os,sys

def oscmd(c):
    os.system(c)

oscmd('sphinx-build -d build/doctrees source build/html')

if sys.platform != 'win32':
    oscmd('sphinx-build -b latex -d build/doctrees source build/latex')
    os.chdir('build/latex')
    oscmd('pdflatex ipython.tex')
    oscmd('pdflatex ipython.tex')
    oscmd('pdflatex ipython.tex')
    oscmd('makeindex -s python.ist ipython.idx')
    oscmd('makeindex -s python.ist modipython.idx')
    oscmd('pdflatex ipython.tex')
    oscmd('pdflatex ipython.tex')
    os.chdir('../..')
