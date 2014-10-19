// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
], function(IPython, $, utils, dialog) {
    var Contents = function(options) {
        // Constructor
        //
        // A contents handles passing file operations
        // to the back-end.  This includes checkpointing
        // with the normal file operations.
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance
        //          base_url: string
        this.events = options.events;
        this.base_url = options.base_url;
    };
 
    /**
     * Notebook Functions
     */

    /**
     * Load a notebook.
     *
     * Calls success_callback with notebook JSON object (as string), or
     * error_callback with error.
     *
     * @method load_notebook
     * @param {String} path
     * @param {String} name
     * @param {Function} success_callback
     * @param {Function} error_callback
     */
    Contents.prototype.load_notebook = function (path, name, success_callback, 
        error_callback) {
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : success_callback,
            error : error_callback,
        };
        this.events.trigger('notebook_loading.Notebook');
        var url = utils.url_join_encode(
            this.base_url,
            'api/contents',
            path,
            name
        );
        $.ajax(url, settings);
    };


    /**
     * Creates a new notebook file at the specified path, and
     * opens that notebook in a new window.
     *
     * @method scroll_to_cell
     * @param {String} path The path to create the new notebook at
     */
    Contents.prototype.new_notebook = function(path) {
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
                        'contents',
                        path,
                        notebook_name
                    ),
                    '_blank'
                );
            },
            error : function(xhr, status, error) {
                utils.log_ajax_error(xhr, status, error);
                var msg;
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    msg = xhr.responseJSON.message;
                } else {
                    msg = xhr.statusText;
                }
                dialog.modal({
                    title : 'Creating Notebook Failed',
                    body : "The error was: " + msg,
                    buttons : {'OK' : {'class' : 'btn-primary'}}
                });
            }
        };
        var url = utils.url_join_encode(
            base_url,
            'api/contents',
            path
        );
        $.ajax(url,settings);
    };

    Contents.prototype.delete_notebook = function(name, path) {
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType : "json",
            success : $.proxy(this.events.trigger, this.events,
                'notebook_deleted.Contents',
                {
                    name: name,
                    path: path
                }),
            error : utils.log_ajax_error
        };
        var url = utils.url_join_encode(
            this.base_url,
            'api/contents',
            path,
            name
        );
        $.ajax(url, settings);
    };

    Contents.prototype.rename_notebook = function(path, name, new_name) {
        var that = this;
        var data = {name: new_name};
        var settings = {
            processData : false,
            cache : false,
            type : "PATCH",
            data : JSON.stringify(data),
            dataType: "json",
            contentType: 'application/json',
            success :  function (json, status, xhr) {
                that.events.trigger('notebook_rename_success.Contents',
                    json);
            },
            error : function (xhr, status, error) {
                that.events.trigger('notebook_rename_error.Contents',
                    [xhr, status, error]);
            }
        };
        var url = utils.url_join_encode(
            this.base_url,
            'api/contents',
            path,
            name
        );
        $.ajax(url, settings);
    };

    Contents.prototype.save_notebook = function(path, name, content,
        extra_settings) {
        var that = content;
        // Create a JSON model to be sent to the server.
        var model = {
            name : name,
            path : path,
            type : "notebook",
            content : content
        };
        // time the ajax call for autosave tuning purposes.
        var start =  new Date().getTime();
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "PUT",
            data : JSON.stringify(model),
            contentType: 'application/json',
            success : $.proxy(this.events.trigger, this.events,
                'notebook_save_success.Contents',
                $.extend(model, { start : start })),
            error : function (xhr, status, error) {
                that.events.trigger('notebook_save_error.Contents',
                    [xhr, status, error, model]);
            }
        };
        if (extra_settings) {
            for (var key in extra_settings) {
                settings[key] = extra_settings[key];
            }
        }
        var url = utils.url_join_encode(
            this.base_url,
            'api/contents',
            path,
            name
        );
        $.ajax(url, settings);
    };

    /**
     * Checkpointing Functions
     */

    Contents.prototype.save_checkpoint = function() {
        // This is not necessary - integrated into save
    };

    Contents.prototype.restore_checkpoint = function(notebook, id) {
        that = notebook;
        this.events.trigger('notebook_restoring.Notebook', checkpoint);
        var url = utils.url_join_encode(
            this.base_url,
            'api/contents',
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
    };

    Contents.prototype.list_checkpoints = function(notebook) {
        that = notebook;
        var url = utils.url_join_encode(
            that.base_url,
            'api/contents',
            that.notebook_path,
            that.notebook_name,
            'checkpoints'
        );
        $.get(url).done(
            $.proxy(that.list_checkpoints_success, that)
        ).fail(
            $.proxy(that.list_checkpoints_error, that)
        );
    };

    /**
     * File management functions
     */

    /**
     * List notebooks and directories at a given path
     *
     * On success, load_callback is called with an array of dictionaries
     * representing individual files or directories.  Each dictionary has
     * the keys:
     *     type: "notebook" or "directory"
     *     name: the name of the file or directory
     *     created: created date
     *     last_modified: last modified dat
     *     path: the path
     * @method list_notebooks
     * @param {String} path The path to list notebooks in
     * @param {Function} load_callback called with list of notebooks on success
     * @param {Function} error_callback called with ajax results on error
     */
    Contents.prototype.list_contents = function(path, load_callback,
        error_callback) {
        var that = this;
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : load_callback,
            error : error_callback
        };

        var url = utils.url_join_encode(this.base_url, 'api', 'contents',
            path);
        $.ajax(url, settings);
    }


    IPython.Contents = Contents;

    return {'Contents': Contents};
}); 
