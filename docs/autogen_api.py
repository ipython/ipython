#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""

import os
import sys

pjoin = os.path.join

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(pjoin(os.path.abspath(here), 'sphinxext'))

from apigen import ApiDocWriter

source = pjoin(here, 'source')

#*****************************************************************************
def main():
    package = 'IPython'
    outdir = pjoin(source, 'api', 'generated')
    docwriter = ApiDocWriter(package,rst_extension='.rst')
    # You have to escape the . here because . is a special char for regexps.
    # You must do make clean if you change this!
    docwriter.package_skip_patterns += [r'\.external$',
                                        # Extensions are documented elsewhere.
                                        r'\.extensions',
                                        # This isn't API
                                        r'\.sphinxext',
                                        # The pt_inputhooks modules often cause
                                        # problems on import, such as trying to
                                        # load incompatible Qt bindings.
                                        r'\.terminal\.pt_inputhooks',
                                        ]

    docwriter.module_skip_patterns += [
        r"\.ipdoctest",
        r"\.testing\.plugin",
        # We document this manually.
        r"\.utils\.py3compat",
        # These are exposed in display
        r"\.core\.display",
        r"\.lib\.display",
        # Private APIs (there should be a lot more here)
        r"\.terminal\.ptutils",
    ]

    # These modules import functions and classes from other places to expose
    # them as part of the public API. They must have __all__ defined. The
    # non-API modules they import from should be excluded by the skip patterns
    # above.
    docwriter.names_from__all__.update(
        {
            "IPython",
            "IPython.display",
        }
    )

    # Now, generate the outputs
    docwriter.write_api_docs(outdir)
    # Write index with .txt extension - we can include it, but Sphinx won't try
    # to compile it
    docwriter.write_index(outdir, 'gen.txt',
                          relative_to = pjoin(source, 'api')
                          )
    print ('%d files written' % len(docwriter.written_modules))


if __name__ == '__main__':
    main()
