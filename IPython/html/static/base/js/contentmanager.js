// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
], function(IPython, $) {
    var ContentManager = function() {
        // Constructor
        //
        // A contentmanager handles passing file operations
        // to the back-end.  This includes checkpointing
        // with the normal file operations.
        //
        // Parameters:
        //        None
        this.version = 0.1;
    }

    ContentManager.prototype.new_notebook = function() {
    }

    ContentManager.prototype.delete_notebook = function(name, path) {
    }

    ContentManager.prototype.rename_notebook = function(new_name, new_path, old_name, old_path) {
    }

    ContentManager.prototype.save_notebook = function(notebook, extra_settings) {
    }

    ContentManager.prototype.save_checkpoint = function() {
    }

    ContentManager.prototype.restore_checkpoint = function(id) {
    }

    ContentManager.prototype.list_checkpoints = function() {
    }

     return ContentManager;
}); 
