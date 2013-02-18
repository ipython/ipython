#!/usr/bin/env python
"""Simple script to auto-generate the index of notebooks in a given directory.
"""

import glob
import urllib

notebooks = sorted(glob.glob('*.ipynb'))

tpl = ( '* [{0}](http://nbviewer.ipython.org/url/github.com/ipython/ipython/'
        'raw/master/examples/notebooks/{1})' )

idx = [ 
"""# A collection of Notebooks for using IPython effectively

The following notebooks showcase multiple aspects of IPython, from its basic
use to more advanced scenarios.  They introduce you to the use of the Notebook
and also cover aspects of IPython that are available in other clients, such as
the cell magics for multi-language integration or our extended display
protocol.

For beginners, we recommend that you start with the 5-part series that
introduces the system, and later read others as the topics interest you.

Once you are familiar with the notebook system, we encourage you to visit our
[gallery](https://github.com/ipython/ipython/wiki/A-gallery-of-interesting-IPython-Notebooks)
where you will find many more examples that cover areas from basic Python
programming to advanced topics in scientific computing.
"""]

idx.extend(tpl.format(nb.replace('.ipynb',''), urllib.quote(nb)) 
           for nb in notebooks)

with open('README.md', 'w') as f:
    f.write('\n'.join(idx))
    f.write('\n')
