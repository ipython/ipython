
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# local import
import sphinx_howto.SphinxHowtoExporter
from IPython.utils.traitlets import Unicode
#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class SphinxManualExporter(sphinx_howto.SphinxHowtoExporter):

    template_file = Unicode(
            'sphinx_manual', config=True,
            help="Name of the template file to use")
    