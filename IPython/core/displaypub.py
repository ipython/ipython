# -*- coding: utf-8 -*-
"""An interface for publishing rich data to frontends.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2010 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config.configurable import Configurable

#-----------------------------------------------------------------------------
# Main payload class
#-----------------------------------------------------------------------------

class DisplayPublisher(Configurable):

    def _validate_data(self, source, data, metadata=None):
        if not isinstance(source, str):
            raise TypeError('source must be a str, got: %r' % source)
        if not isinstance(data, dict):
            raise TypeError('data must be a dict, got: %r' % data)
        if metadata is not None:
            if not isinstance(metadata, dict):
                raise TypeError('metadata must be a dict, got: %r' % data)

    def publish(self, source, data, metadata=None):
        """Publish data and metadata to all frontends.

        See the ``display_data`` message in the messaging documentation for
        more details about this message type.

        Parameters
        ----------
        source : str
            A string that give the function or method that created the data,
            such as 'IPython.core.page'.
        data : dict
            A dictionary having keys that are valid MIME types (like 
            'text/plain' or 'image/svg+xml') and values that are the data for
            that MIME type. The data itself must be a JSON'able data
            structure. Minimally all data should have the 'text/plain' data,
            which can be displayed by all frontends. If more than the plain
            text is given, it is up to the frontend to decide which
            representation to use.
        metadata : dict
            A dictionary for metadata related to the data. This can contain
            arbitrary key, value pairs that frontends can use to interpret
            the data.
        """
        from IPython.utils import io
        # The default is to simply write the plain text data using io.Term.
        if data.has_key('text/plain'):
            print >>io.Term.cout, data['text/plain']


def publish_display_data(source, text, svg=None, png=None,
                         html=None, metadata=None):
    """Publish a display data to the frontends.

    This function is a high level helper for the publishing of display data.
    It handle a number of common MIME types in a clean API. For other MIME
    types, use ``get_ipython().display_pub.publish`` directly.

    Parameters
    ----------
    text : str/unicode
        The string representation of the plot.

    svn : str/unicode
        The raw svg data of the plot.

    png : ???
        The raw png data of the plot.

    metadata : dict, optional [default empty]
        Allows for specification of additional information about the plot data.
    """
    from IPython.core.interactiveshell import InteractiveShell

    data_dict = {}
    data_dict['text/plain'] = text
    if svg is not None:
        data_dict['image/svg+xml'] = svg
    if png is not None:
        data_dict['image/png'] = png
    if html is not None:
        data_dict['text/html'] = html
    InteractiveShell.instance().display_pub.publish(
        source,
        data_dict,
        metadata
    )
