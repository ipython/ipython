// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
    'bootstrap',
], function(IPython, $, utils, dialog, bootstrap) {
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
        var that = this;
        var editor = that.editor;
        
        //  File
        this.element.find('#new-file').click(function () {
            var w = window.open();
            // Create a new file in the current directory
            var parent = utils.url_path_split(editor.file_path)[0];
            editor.contents.new_untitled(parent, {type: "file"}).then(
                function (data) {
                    w.location = utils.url_join_encode(
                        that.base_url, 'edit', data.path
                    );
                },
                function(error) {
                    w.close();
                    dialog.modal({
                        title : 'Creating New File Failed',
                        body : "The error was: " + error.message,
                        buttons : {'OK' : {'class' : 'btn-primary'}}
                    });
                }
            );
        });
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
        this.element.find('#menu-keymap-default').click(function () {
            editor.update_codemirror_options({
                vimMode: false,
                keyMap: null
            });
        });
        this.element.find('#menu-keymap-sublime').click(function () {
            editor.update_codemirror_options({
                vimMode: false,
                keyMap: 'sublime'
            });
        });
        this.element.find('#menu-keymap-emacs').click(function () {
            editor.update_codemirror_options({
                vimMode: false,
                keyMap: 'emacs'
            });
        });
        this.element.find('#menu-keymap-vim').click(function () {
            editor.update_codemirror_options({
                vimMode: true,
                keyMap: 'vim'
            });
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
            var keyMap = editor.codemirror.getOption('keyMap') || "default";
            that.element.find(".selected-keymap").removeClass("selected-keymap");
            that.element.find("#menu-keymap-" + keyMap).addClass("selected-keymap");
        });
    };

    return {'MenuBar': MenuBar};
});
