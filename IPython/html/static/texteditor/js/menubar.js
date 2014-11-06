// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'bootstrap',
], function(IPython, $, utils, bootstrap) {
    "use strict";
    
    var MenuBar = function (selector, options) {
        // Constructor
        //
        // A MenuBar Class to generate the menubar of IPython notebook
        //
        // Parameters:
        //  selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          codemirror: CodeMirror instance
        //          contents: ContentManager instance
        //          events: $(Events) instance
        //          base_url : string
        //          file_path : string
        options = options || {};
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.selector = selector;
        this.codemirror = options.codemirror;
        this.contents = options.contents;
        this.events = options.events;
        this.file_path = options.file_path;

        if (this.selector !== undefined) {
            this.element = $(selector);
            this.bind_events();
        }
    };

    MenuBar.prototype.bind_events = function () {
        //  File
        var that = this;
        this.element.find('#save_file').click(function () {
            var ix = that.file_path.lastIndexOf("/");
            var dir_path, basename;
            if (ix === -1) {
                dir_path = '';
                basename = that.file_path;
            } else {
                dir_path = that.file_path.substring(0, ix);
                basename = that.file_path.substring(ix+1);
            }
            var model = {
                path: dir_path,
                name: basename,
                type: 'file',
                format: 'text',
                content: that.codemirror.getValue(),
            };
            console.log(model);
            that.contents.save(dir_path, basename, model, {
                success: function() {
                    that.events.trigger("save_succeeded.TextEditor");
                }
            });
        });
    };

    return {'MenuBar': MenuBar};
});
