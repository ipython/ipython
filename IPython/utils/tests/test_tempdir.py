#-----------------------------------------------------------------------------
#  Copyright (C) 2012-  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import os

from IPython.utils.tempdir import NamedFileInTemporaryDirectory


def test_named_file_in_temporary_directory():
    with NamedFileInTemporaryDirectory('filename') as file:
        name = file.name
        assert not file.closed
        assert os.path.exists(name)
        file.write('test')
    assert file.closed
    assert not os.path.exists(name)
