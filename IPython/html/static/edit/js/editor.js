// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/utils',
    'codemirror/lib/codemirror',
    'codemirror/mode/meta',
    'codemirror/addon/comment/comment',
    'codemirror/addon/dialog/dialog',
    'codemirror/addon/edit/closebrackets',
    'codemirror/addon/edit/matchbrackets',
    'codemirror/addon/search/searchcursor',
    'codemirror/addon/search/search',
    'codemirror/keymap/emacs',
    'codemirror/keymap/sublime',
    'codemirror/keymap/vim',
    ],
function($,
    utils,
    CodeMirror
) {
    "use strict";
    
    var Editor = function(selector, options) {
        var that = this;
        this.selector = selector;
        this.contents = options.contents;
        this.events = options.events;
        this.base_url = options.base_url;
        this.file_path = options.file_path;
        this.config = options.config;
        this.codemirror = new CodeMirror($(this.selector)[0]);
        this.generation = -1;
        
        // It appears we have to set commands on the CodeMirror class, not the
        // instance. I'd like to be wrong, but since there should only be one CM
        // instance on the page, this is good enough for now.
        CodeMirror.commands.save = $.proxy(this.save, this);
        
        this.save_enabled = false;
        
        this.config.loaded.then(function () {
            // load codemirror config
            var cfg = that.config.data.Editor || {};
            var cmopts = $.extend(true, {}, // true = recursive copy
                Editor.default_codemirror_options,
                cfg.codemirror_options || {}
            );
            that._set_codemirror_options(cmopts);
            that.events.trigger('config_changed.Editor', {config: that.config});
        });
    };
    
    // default CodeMirror options
    Editor.default_codemirror_options = {
        extraKeys: {
            "Tab" :  "indentMore",
        },
        indentUnit: 4,
        theme: "ipython",
        lineNumbers: true,
    };
    
    Editor.prototype.load = function() {
        /** load the file */
        var that = this;
        var cm = this.codemirror;
        return this.contents.get(this.file_path, {type: 'file', format: 'text'})
            .then(function(model) {
                cm.setValue(model.content);

                // Setting the file's initial value creates a history entry,
                // which we don't want.
                cm.clearHistory();

                // Find and load the highlighting mode
                utils.requireCodeMirrorMode(model.mimetype, function(spec) {
                    var mode = CodeMirror.getMode({}, spec);
                    cm.setOption('mode', mode);
                });
                that.save_enabled = true;
                that.generation = cm.changeGeneration();
            },
            function(error) {
                cm.setValue("Error! " + error.message +
                                "\nSaving disabled.");
                that.save_enabled = false;
            }
        );
    };

    Editor.prototype.save = function() {
        /** save the file */
        if (!this.save_enabled) {
            console.log("Not saving, save disabled");
            return;
        }
        var model = {
            path: this.file_path,
            type: 'file',
            format: 'text',
            content: this.codemirror.getValue(),
        };
        var that = this;
        // record change generation for isClean
        this.generation = this.codemirror.changeGeneration();
        return this.contents.save(this.file_path, model).then(function() {
            that.events.trigger("save_succeeded.TextEditor");
        });
    };
    
    Editor.prototype._set_codemirror_options = function (options) {
        // update codemirror options from a dict
        for (var opt in options) {
            if (!options.hasOwnProperty(opt)) {
                continue;
            }
            var value = options[opt];
            if (value === null) {
                value = CodeMirror.defaults[opt];
            }
            this.codemirror.setOption(opt, value);
        }
    };
    
    Editor.prototype.update_codemirror_options = function (options) {
        /** update codemirror options locally and save changes in config */
        var that = this;
        this._set_codemirror_options(options);
        return this.config.update({
            Editor: {
                codemirror_options: options
            }
        }).then(
            that.events.trigger('config_changed.Editor', {config: that.config})
        );
    };

    return {Editor: Editor};
});
