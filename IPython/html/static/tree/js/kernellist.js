// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'tree/js/notebooklist',
], function(IPython, $, NotebookList) {
    "use strict";

    var KernelList = function (selector, options, session_list) {
        NotebookList.call(this, selector, options, 'running', session_list);
    };

    KernelList.prototype = Object.create(NotebookList.prototype);

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
    };
    
    // Backwards compatability.
    IPython.KernelList = KernelList;

    return {'KernelList': KernelList};
});
