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
    # You have to escape the . here because . is a special char for regexps.
    # You must do make clean if you change this!
    docwriter.package_skip_patterns += [r'\.fixes$',
                                        r'\.external$',
                                        r'\.extensions',
                                        r'\.kernel\.config',
                                        r'\.attic',
                                        r'\.quarantine',
                                        r'\.deathrow',
                                        r'\.config\.default',
                                        r'\.config\.profile',
                                        r'\.frontend',
                                        r'\.gui',
                                        r'\.kernel',
                                        # For now, the zmq code has
                                        # unconditional top-level code so it's
                                        # not import safe.  This needs fixing
                                        r'\.zmq',
                                        ]

    docwriter.module_skip_patterns += [ r'\.core\.fakemodule',
                                        r'\.testing\.iptest',
                                        # Keeping these disabled is OK
                                        r'\.parallel\.controller\.mongodb',
                                        r'\.lib\.inputhookwx',
                                        r'\.lib\.inputhookgtk',
                                        r'\.cocoa',
                                        r'\.ipdoctest',
                                        r'\.Gnuplot',
                                        r'\.frontend\.process\.winprocess',
                                        r'\.Shell',
                                        ]
    
    # If we don't have pexpect, we can't load irunner, so skip any code that
    # depends on it
    try:
        import pexpect
    except ImportError:
        docwriter.module_skip_patterns += [r'\.lib\.irunner',
                                           r'\.testing\.mkdoctests']
    # Now, generate the outputs
    docwriter.write_api_docs(outdir)
    # Write index with .rst extension - we can include it, but Sphinx won't try
    # to compile it
    docwriter.write_index(outdir, 'gen.rst',
                          relative_to = pjoin('source','api')
                          )
    print '%d files written' % len(docwriter.written_modules)
