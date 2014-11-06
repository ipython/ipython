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
        
        this.save_enabled = true;
    };
    
    // TODO: Remove this once the contents API is refactored to just use paths
    Editor.prototype._split_path = function() {
        var ix = this.file_path.lastIndexOf("/");
        if (ix === -1) {
            return ['', this.file_path];
        } else {
            return [
                this.file_path.substring(0, ix),
                this.file_path.substring(ix+1)
            ];
        }
    };
    
    Editor.prototype.load = function() {
        var split_path = this._split_path();
        var cm = this.codemirror;
        this.contents.load(split_path[0], split_path[1], {
            success: function(model) {
                if (model.type === "file" && model.format === "text") {
                    cm.setValue(model.content);
                    
                    // Find and load the highlighting mode
                    var modeinfo = CodeMirror.findModeByMIME(model.mimetype);
                    if (modeinfo) {
                        utils.requireCodeMirrorMode(modeinfo.mode, function() {
                            cm.setOption('mode', modeinfo.mode);
                        });
                    }
                } else {
                    this.codemirror.setValue("Error! Not a text file. Saving disabled.");
                    this.save_enabled = false;
                }
            }
        });
    };

    Editor.prototype.save = function() {
        var split_path = this._split_path();
        var model = {
            path: split_path[0],
            name: split_path[1],
            type: 'file',
            format: 'text',
            content: this.codemirror.getValue(),
        };
        var that = this;
        this.contents.save(split_path[0], split_path[1], model, {
            success: function() {
                that.events.trigger("save_succeeded.TextEditor");
            }
        });
    };

    return {Editor: Editor};
});
