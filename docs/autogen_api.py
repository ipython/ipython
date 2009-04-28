#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os
import sys

# local imports
sys.path.append(os.path.abspath('sphinxext'))
from apigen import ApiDocWriter

#*****************************************************************************
if __name__ == '__main__':
    pjoin = os.path.join
    package = 'IPython'
    outdir = pjoin('source','api','generated')
    docwriter = ApiDocWriter(package,rst_extension='.txt')
    docwriter.package_skip_patterns += [r'\.fixes$',
                                        r'\.externals$',
                                        r'\.Extensions',
                                        r'\.kernel.config',
                                        r'\.attic',
                                        ]
    docwriter.module_skip_patterns += [ r'\.FakeModule',
                                        r'\.cocoa',
                                        r'\.ipdoctest',
                                        r'\.Gnuplot',
                                        r'\.frontend.process.winprocess',
                                        ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen',
                          relative_to = pjoin('source','api')
                          )
    print '%d files written' % len(docwriter.written_modules)
