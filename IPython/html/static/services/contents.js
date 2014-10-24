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
        //          base_url: string
        this.base_url = options.base_url;
    };

    Contents.prototype.api_url = function() {
        var url_parts = [this.base_url, 'api/contents'].concat(
                                Array.prototype.slice.apply(arguments));
        return utils.url_join_encode.apply(null, url_parts);
    };

    /**
     * File Functions (including notebook operations)
     */

    /**
     * Load a file.
     *
     * Calls success with file JSON model, or error with error.
     *
     * @method load_notebook
     * @param {String} path
     * @param {String} name
     * @param {Function} success
     * @param {Function} error
     */
    Contents.prototype.load_file = function (path, name, options) {
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : options.success,
            error : options.error || function() {}
        };
        var url = this.api_url(path, name);
        $.ajax(url, settings);
    };


    /**
     * Creates a new notebook file at the specified directory path.
     *
     * @method scroll_to_cell
     * @param {String} path The path to create the new notebook at
     */
    Contents.prototype.new_notebook = function(path, options) {
        var error = options.error || function() {};
        var settings = {
            processData : false,
            cache : false,
            type : "POST",
            dataType : "json",
            success : options.success || function() {},
            error : options.error || function() {}
        };
        $.ajax(this.api_url(path), settings);
    };

    Contents.prototype.delete_file = function(name, path, options) {
        var error = options.error || function() {};
        var that = this;
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType : "json",
            success : options.success || function() {},
            error : function(xhr, status, error) {
                utils.log_ajax_error(xhr, status, error);
                error(xhr, status, error);
            }
        };
        var url = this.api_url(path, name);
        $.ajax(url, settings);
    };

    Contents.prototype.rename_file = function(path, name, new_path, new_name, options) {
        var data = {name: new_name, path: new_path};
        var settings = {
            processData : false,
            cache : false,
            type : "PATCH",
            data : JSON.stringify(data),
            dataType: "json",
            contentType: 'application/json',
            success : options.success || function() {}, 
            error : options.error || function() {}
        };
        var url = this.api_url(path, name);
        $.ajax(url, settings);
    };

    Contents.prototype.save_file = function(path, name, model, options) {
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "PUT",
            data : JSON.stringify(model),
            contentType: 'application/json',
            success : options.success || function() {},
            error : options.error || function() {}
        };
        if (options.extra_settings) {
            $.extend(settings, options.extra_settings);
        }
        var url = this.api_url(path, name);
        $.ajax(url, settings);
    };

    /**
     * Checkpointing Functions
     */

    Contents.prototype.create_checkpoint = function(path, name, options) {
        var url = this.api_url(path, name, 'checkpoints');
        var settings = {
            type : "POST",
            success: options.success || function() {},
            error: options.error || function() {}
        };
        $.ajax(url, settings);
    };

    Contents.prototype.list_checkpoints = function(path, name, options) {
        var url = this.api_url(path, name, 'checkpoints');
        var settings = {
            type : "GET",
            success: options.success,
            error: options.error || function() {}
        };
        $.ajax(url, settings);
    };

    Contents.prototype.restore_checkpoint = function(path, name, checkpoint_id, options) {
        var url = this.api_url(path, name, 'checkpoints', checkpoint_id);
        var settings = {
            type : "POST",
            success: options.success || function() {},
            error: options.error || function() {}
        };
        $.ajax(url, settings);
    };

    Contents.prototype.delete_checkpoint = function(path, name, checkpoint_id, options) {        
        var url = this.api_url(path, name, 'checkpoints', checkpoint_id);
        var settings = {
            type : "DELETE",
            success: options.success || function() {},
            error: options.error || function() {}
        };
        $.ajax(url, settings);
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
     * @param {Function} error called with ajax results on error
     */
    Contents.prototype.list_contents = function(path, options) {
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : options.success,
            error : options.error || function() {}
        };

        $.ajax(this.api_url(path), settings);
    };


    IPython.Contents = Contents;

    return {'Contents': Contents};
}); 
