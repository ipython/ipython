# -*- coding: utf-8 -*-
"""Notebook related utilities

Authors:

* Brian Granger
* Martín Gaitán
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import docutils.core
import docutils.io
try:
    from rst2html5 import HTML5Writer
except ImportError:
    HTML5Writer = None


def rst2html(source):
    writer = HTML5Writer() if HTML5Writer else None
    output, pub = docutils.core.publish_programmatically(
        source=source, source_path=None,
        source_class=docutils.io.StringInput,
        destination_class=docutils.io.StringOutput,
        destination=None,
        destination_path=None,
        reader=None, reader_name='standalone',
        parser=None, parser_name='restructuredtext',
        writer=writer, writer_name='html',
        settings=None, settings_spec=None,
        settings_overrides=None,
        config_section=None,
        enable_exit_status=None)
    return pub.writer.parts['body']


def url_path_join(*pieces):
    """Join components of url into a relative url

    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place
    """
    initial = pieces[0].startswith('/')
    final = pieces[-1].endswith('/')
    striped = [s.strip('/') for s in pieces]
    result = '/'.join(s for s in striped if s)
    if initial: result = '/' + result
    if final: result = result + '/'
    if result == '//': result = '/'
    return result
