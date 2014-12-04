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
        this.element.find('#save_file').click(function () {
            that.editor.save();
        });
    };

    return {'MenuBar': MenuBar};
});
