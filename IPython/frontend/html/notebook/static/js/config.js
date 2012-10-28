//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Notebook
//============================================================================

var IPython = (function (IPython) {

    var config = {
        cell_magic_highlight : {
              'magic_javascript':{'reg':[/^%%javascript/]}
             ,'magic_perl'      :{'reg':[/^%%perl/]}
             ,'magic_ruby'      :{'reg':[/^%%ruby/]}
             ,'magic_python'    :{'reg':[/^%%python3?/]}
             ,'magic_shell'      :{'reg':[/^%%bash/]}
             ,'magic_r'         :{'reg':[/^%%R/]}
            },
        raw_cell_highlight : {
             'diff'         :{'reg':[/^diff/]}
            }
        };

    IPython.config = config;

    return IPython;

}(IPython));

