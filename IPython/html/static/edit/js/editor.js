// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/utils',
    'codemirror/lib/codemirror',
    'codemirror/mode/meta',
    'codemirror/addon/search/search'
    ],
function($,
    utils,
    CodeMirror
) {
    var Editor = function(selector, options) {
        this.selector = selector;
        this.contents = options.contents;
        this.events = options.events;
        this.base_url = options.base_url;
        this.file_path = options.file_path;
        
        this.codemirror = CodeMirror($(this.selector)[0]);
        
        // It appears we have to set commands on the CodeMirror class, not the
        // instance. I'd like to be wrong, but since there should only be one CM
        // instance on the page, this is good enough for now.
        CodeMirror.commands.save = $.proxy(this.save, this);
        
        this.save_enabled = false;
    };
    
    Editor.prototype.load = function() {
        var that = this;
        var cm = this.codemirror;
        this.contents.get(this.file_path, {type: 'file', format: 'text'})
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
            },
            function(error) {
                cm.setValue("Error! " + error.message +
                                "\nSaving disabled.");
                that.save_enabled = false;
            }
        );
    };

    Editor.prototype.save = function() {
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
        this.contents.save(this.file_path, model).then(function() {
            that.events.trigger("save_succeeded.TextEditor");
        });
    };

    return {Editor: Editor};
});
