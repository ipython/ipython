// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'tree/js/notebooklist',
], function(IPython, $, notebooklist) {
    "use strict";

    var KernelList = function (selector, options) {
        /**
         * Constructor
         *
         * Parameters:
         *  selector: string
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          session_list: SessionList instance
         *          base_url: string
         *          notebook_path: string
         */
        notebooklist.NotebookList.call(this, selector, $.extend({
            element_name: 'running'},
            options));
    };

    KernelList.prototype = Object.create(notebooklist.NotebookList.prototype);

    KernelList.prototype.add_duplicate_button = function () {
        /**
         * do nothing
         */
    };
    
    KernelList.prototype.sessions_loaded = function (d) {
        this.sessions = d;
        this.clear_list();
        var item, path;
        for (path in d) {
            if (!d.hasOwnProperty(path)) {
                // nothing is safe in javascript
                continue;
            }
            item = this.new_item(-1);
            this.add_link({
                name: path,
                path: path,
                type: 'notebook',
            }, item);
        }
        $('#running_list_header').toggle($.isEmptyObject(d));
    };
    
    // Backwards compatability.
    IPython.KernelList = KernelList;

    return {'KernelList': KernelList};
});
