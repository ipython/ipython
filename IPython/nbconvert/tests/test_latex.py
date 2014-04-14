# -*- coding: utf-8 -*- 
"""Test Latex in NbConvertApp"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import textwrap
from IPython.nbformat import current

from .base import TestsBase

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestNbConvertLatex(TestsBase):
    """Collection of NbConvert Latex tests"""

    def test_very_long_cells(self):
        """
        Torture test that long cells do not cause issues
        """
        lorem_ipsum_text = textwrap.dedent("""\
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec
          dignissim, ipsum non facilisis tempus, dui felis tincidunt metus,
          nec pulvinar neque odio eget risus. Nulla nisi lectus, cursus
          suscipit interdum at, ultrices sit amet orci. Mauris facilisis
          imperdiet elit, vitae scelerisque ipsum dignissim non. Integer
          consequat malesuada neque sit amet pulvinar. Curabitur pretium
          ut turpis eget aliquet. Maecenas sagittis lacus sed lectus
          volutpat, eu adipiscing purus pulvinar. Maecenas consequat
          luctus urna, eget cursus quam mollis a. Aliquam vitae ornare
          erat, non hendrerit urna. Sed eu diam nec massa egestas pharetra
          at nec tellus. Fusce feugiat lacus quis urna sollicitudin volutpat.
          Quisque at sapien non nibh feugiat tempus ac ultricies purus.
           """)
        lorem_ipsum_text = lorem_ipsum_text.replace("\n"," ") + "\n\n"
        large_lorem_ipsum_text = "".join([lorem_ipsum_text]*3000)

        notebook_name = "lorem_ipsum_long.ipynb"
        tex_name = "lorem_ipsum_long.tex"
        with self.create_temp_cwd([]):
            nb = current.new_notebook(
                worksheets=[
                    current.new_worksheet(cells=[
                        current.new_text_cell('markdown',source=large_lorem_ipsum_text)
                    ])
                ]
            )
            with open(notebook_name, 'w') as f: current.write(nb, f, 'ipynb')
            self.call('nbconvert --to latex --log-level 0 ' + 
                      os.path.join(notebook_name))
            assert os.path.isfile(tex_name)


