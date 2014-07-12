// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
], function(IPython, $) {
    var ContentManager = function(notebook_path, base_url) {
        // Constructor
        //
        // A contentmanager handles passing file operations
        // to the back-end.  This includes checkpointing
        // with the normal file operations.
        //
        // Parameters:
        //        notebook_path
        //        base_url
        this.version = 0.1;
        this.notebook_path = notebook_path;
        this.base_url = base_url;
    }

    ContentManager.prototype.new_notebook = function() {
        var path = this.notebook_path;
        var base_url = this.base_url;
        var settings = {
            processData : false,
            cache : false,
            type : "POST",
            dataType : "json",
            async : false,
            success : function (data, status, xhr){
                var notebook_name = data.name;
                window.open(
                    utils.url_join_encode(
                        base_url,
                        'notebooks',
                        path,
                        notebook_name
                    ),
                    '_blank'
                );
            },
            error : utils.log_ajax_error,
        };
        var url = utils.url_join_encode(
            base_url,
            'api/notebooks',
            path
        );
        $.ajax(url,settings);
    }

    ContentManager.prototype.delete_notebook = function(notebook) {
        var that = notebook;
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType: "json",
            error : utils.log_ajax_error,
        };
        var url = utils.url_join_encode(
            that.base_url,
            'api/notebooks',
            that.notebook_path,
            that.notebook_name
        );
        $.ajax(url, settings);
    }

    ContentManager.prototype.rename_notebook = function(notebook, nbname) {
        var that = notebook;
        if (!nbname.match(/\.ipynb$/)) {
            nbname = nbname + ".ipynb";
        }
        var data = {name: nbname};
        var settings = {
            processData : false,
            cache : false,
            type : "PATCH",
            data : JSON.stringify(data),
            dataType: "json",
            headers : {'Content-Type': 'application/json'},
            success : $.proxy(that.rename_success, this),
            error : $.proxy(that.rename_error, this)
        };
        this.events.trigger('rename_notebook.Notebook', data);
        var url = utils.url_join_encode(
            this.base_url,
            'api/notebooks',
            this.notebook_path,
            this.notebook_name
        );
        $.ajax(url, settings);
    }

    ContentManager.prototype.save_notebook = function(notebook, extra_settings) {
        // Create a JSON model to be sent to the server.
        var model = {};
        model.name = notebook.notebook_name;
        model.path = notebook.notebook_path;
        model.content = notebook.toJSON();
        model.content.nbformat = notebook.nbformat;
        model.content.nbformat_minor = notebook.nbformat_minor;
        // time the ajax call for autosave tuning purposes.
        var start =  new Date().getTime();
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "PUT",
            data : JSON.stringify(model),
            headers : {'Content-Type': 'application/json'},
            success : $.proxy(notebook.save_notebook_success, this, start),
            error : $.proxy(notebook.save_notebook_error, this)
        };
        if (extra_settings) {
            for (var key in extra_settings) {
                settings[key] = extra_settings[key];
            }
        }
        notebook.events.trigger('notebook_saving.Notebook');
        var url = utils.url_join_encode(
            notebook.base_url,
            'api/notebooks',
            notebook.notebook_path,
            notebook.notebook_name
        );
        $.ajax(url, settings);
    };
     }

    ContentManager.prototype.save_checkpoint = function() {
        // This is not necessary - integrated into save
    }

    ContentManager.prototype.restore_checkpoint = function(notebook, id) {
        that = notebook;
        this.events.trigger('notebook_restoring.Notebook', checkpoint);
        var url = utils.url_join_encode(
            this.base_url,
            'api/notebooks',
            this.notebook_path,
            this.notebook_name,
            'checkpoints',
            checkpoint
        );
        $.post(url).done(
            $.proxy(that.restore_checkpoint_success, that)
        ).fail(
            $.proxy(that.restore_checkpoint_error, that)
        );
    }

    ContentManager.prototype.list_checkpoints = function(notebook) {
        that = notebook;
        var url = utils.url_join_encode(
            that.base_url,
            'api/notebooks',
            that.notebook_path,
            that.notebook_name,
            'checkpoints'
        );
        $.get(url).done(
            $.proxy(that.list_checkpoints_success, that)
        ).fail(
            $.proxy(that.list_checkpoints_error, that)
        );
    }

    return ContentManager;
}); 
