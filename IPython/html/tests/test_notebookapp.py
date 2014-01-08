"""Test NotebookApp"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import nose.tools as nt

import IPython.testing.tools as tt
from IPython.html import notebookapp

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_help_output():
    """ipython notebook --help-all works"""
    tt.help_all_output_test('notebook')

def test_server_info_file():
    nbapp = notebookapp.NotebookApp(profile='nbserver_file_test')
    def get_servers():
        return list(notebookapp.discover_running_servers(profile='nbserver_file_test'))
    nbapp.initialize(argv=[])
    nbapp.write_server_info_file()
    servers = get_servers()
    nt.assert_equal(len(servers), 1)
    nt.assert_equal(servers[0]['port'], nbapp.port)
    nt.assert_equal(servers[0]['url'], nbapp.connection_url)
    nbapp.remove_server_info_file()
    nt.assert_equal(get_servers(), [])

    # The ENOENT error should be silenced.
    nbapp.remove_server_info_file()