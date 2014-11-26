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
        /**
         * Constructor
         *
         * A MenuBar Class to generate the menubar of IPython notebook
         *
         * Parameters:
         *  selector: string
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          codemirror: CodeMirror instance
         *          contents: ContentManager instance
         *          events: $(Events) instance
         *          base_url : string
         *          file_path : string
         */
        options = options || {};
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.selector = selector;
        this.editor = options.editor;
        this.events = options.events;

        if (this.selector !== undefined) {
            this.element = $(selector);
            this.bind_events();
        }
    };

    MenuBar.prototype.bind_events = function () {
        /**
         *  File
         */
        var that = this;
        var editor = that.editor;
        this.element.find('#save-file').click(function () {
            editor.save();
        });
        
        // Edit
        this.element.find('#menu-find').click(function () {
            editor.codemirror.execCommand("find");
        });
        this.element.find('#menu-replace').click(function () {
            editor.codemirror.execCommand("replace");
        });
        
        // View
        this.element.find('#menu-line-numbers').click(function () {
            var current = editor.codemirror.getOption('lineNumbers');
            var value = Boolean(1-current);
            editor.update_codemirror_options({lineNumbers: value});
        });
        
        this.events.on("config_changed.Editor", function () {
            var lineNumbers = editor.codemirror.getOption('lineNumbers');
            var text = lineNumbers ? "Hide" : "Show";
            text = text + " Line Numbers";
            that.element.find('#menu-line-numbers').find("a").text(text);
        });
    };

    return {'MenuBar': MenuBar};
});
