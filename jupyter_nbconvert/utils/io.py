# coding: utf-8
"""io-related utilities"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import codecs
import sys
from IPython.utils.py3compat import PY3


def unicode_std_stream(stream='stdout'):
    u"""Get a wrapper to write unicode to stdout/stderr as UTF-8.

    This ignores environment variables and default encodings, to reliably write
    unicode to stdout or stderr.

    ::

        unicode_std_stream().write(u'ł@e¶ŧ←')
    """
    assert stream in ('stdout', 'stderr')
    stream  = getattr(sys, stream)
    if PY3:
        try:
            stream_b = stream.buffer
        except AttributeError:
            # sys.stdout has been replaced - use it directly
            return stream
    else:
        stream_b = stream

    return codecs.getwriter('utf-8')(stream_b)
