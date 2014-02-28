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

    var utils = IPython.utils;

    var KernelList = function (selector, options) {
        IPython.NotebookList.call(this, selector, options, 'running');
    };

    KernelList.prototype = Object.create(IPython.NotebookList.prototype);

    KernelList.prototype.sessions_loaded = function (d) {
        this.sessions = d;
        this.clear_list();
        var item;
        for (var path in d) {
            item = this.new_notebook_item(-1);
            this.add_link('', path, item);
            this.add_shutdown_button(item, this.sessions[path]);
        }
       
        $('#running_list_header').toggle($.isEmptyObject(d));
    }
    
    IPython.KernelList = KernelList;

    return IPython;

}(IPython));
