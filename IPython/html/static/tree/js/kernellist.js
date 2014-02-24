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
        // clear out the previous list
        this.clear_list();
        var len  = d.length;
        var item;
        for (var i=0; i < d.length; i++) {
            var path= utils.url_path_join(d[i].notebook.path, d[i].notebook.name);
            item = this.new_notebook_item(i);
            this.add_link('', path, item);
            this.sessions[path] = d[i].id;
            this.add_shutdown_button(item,this.sessions[path]);
        }
       
        if (len > 0) {
           $('#' + this.element_name + '_list_header').hide();
       } else {
           $('#' + this.element_name + '_list_header').show();
       }
    }
    
    IPython.KernelList = KernelList;

    return IPython;

}(IPython));
