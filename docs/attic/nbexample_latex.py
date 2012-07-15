from notebook.markup import latex

latex.document_class('article')
latex.title('This is a Python Notebook')

latex.section('A section title',label='sec:intro')

latex.text(r"""Below, we define a simple function
\begin{equation}
f: (x,y) \rightarrow x+y^2
\end{equation}""")

def f(x,y):
    return x+y**2

# since the .text method passes directly to latex, all markup could be input
# in that way if so desired
latex.text(r"""
\section{Another section}

More text...

And now a picture showing our important results...""")

latex.include_graphic('foo.png')
