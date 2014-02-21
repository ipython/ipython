//----------------------------------------------------------------------------
//  Copyright (C) 2014  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Running Kernels List
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    
    var KernelList = function (selector, options) {
        IPython.NotebookList.call(this, selector, options);
    };

    KernelList.prototype = IPython.NotebookList.prototype;

    IPython.KernelList = KernelList;

    return IPython;

}(IPython));
