// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
], function(IPython, $, utils, dialog) {
    var FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder';
        
    var ContentManager = function(options) {
        // Constructor
        //
        // A contentmanager handles passing file operations
        // to the back-end.  This includes checkpointing
        // with the normal file operations.
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance
        //          base_url: string
        var that = this;
        this.version = 0.1;
        this.events = options.events;
        this.base_url = options.base_url;
        this.gapi_ready = $.Deferred();

        this.gapi_ready.fail(function(){
            // TODO: display a dialog
            console.log('failed to load Google API');
        });

        // load Google API
        $.getScript('https://apis.google.com/js/client.js');
        function poll_for_gapi_load() {
            if (window.gapi && gapi.client) {
                that.on_gapi_load();
            } else {
                setTimeout(poll_for_gapi_load, 100);
            }
        }
        poll_for_gapi_load();
    };

    /**
     * low level Google Drive functions
     */

    /*
     * Load Google Drive client library
     * @method on_gapi_load
     */
    ContentManager.prototype.on_gapi_load = function() {
        var that = this;
        gapi.load('auth:client,drive-realtime,drive-share', function() {
            gapi.client.load('drive', 'v2', function() {
                that.authorize(false);
            });
        });
    };

    /**
     * Authorize using Google OAuth API.
     * @method authorize
     * @param {boolean} opt_withPopup If true, display popup without first
     *     trying to authorize without a popup.
     */
    ContentManager.prototype.authorize = function(opt_withPopup) {
        var that = this;
        var doAuthorize = function() {
            gapi.auth.authorize({
                'client_id': '911569945122-tlvi6ucbj137ifhitpqpdikf3qo1mh9d.apps.googleusercontent.com',
                'scope': ['https://www.googleapis.com/auth/drive'],
                'immediate': !opt_withPopup
            }, function(response) {
                if (!response || response['error']) {
                    if (opt_withPopup) {
                        that.gapi_ready.reject(response ? response['error'] : null);
                    } else {
                        that.authorize(true);
                    }
                    return;
                }
                that.gapi_ready.resolve();
            });
        };

        // if no popup, calls the authorization function immediately
        if (!opt_withPopup) {
            doAuthorize();
            return;
        }

        // Gets user to initiate the authorization with a dialog,
        // to prevent popup blockers.
        var options = {
            title: 'Authentication needed',
            body: ('Accessing Google Drive requires authentication.  Click'
                + ' ok to proceed.'),
            buttons: {
                'ok': { click : doAuthorize },
                'cancel': { click : that.gapi_ready.reject }
            }
        }
        dialog.modal(options);
    };

    /**
     * Gets the Google Drive folder ID corresponding to a path.  Since
     * the Google Drive API doesn't expose a path structure, it is necessary
     * to manually walk the path from root.
     */
    ContentManager.prototype.get_id_for_path = function(path, onSuccess, onFailure) {
        // Use recursive strategy, with helper function
        // get_id_for_relative_path.

        // calls callbacks with the id for the sepcified path, treated as
        // a relative path with base given by base_id.
        function get_id_for_relative_path(base_id, path_components) {
            if (path_components.length == 0) {
                onSuccess(base_id);
                return;
            }

            var this_component = path_components.pop();

            // Treat the empty string as a special case, and ignore it.
            // This will result in ignoring leading and trailing slashes.
            if (this_component == "") {
                get_id_for_relative_path(base_id, path_components);
                return;
            }

            var query = ('mimeType = \'' + FOLDER_MIME_TYPE + '\''
                + ' and title = \'' + this_component + '\'');
            var request = gapi.client.drive.children.list({
                'folderId': base_id,
                'q': query
            });
            request.execute(function(response) {
                if (!response || response['error']) {
                    onFailure(response ? response['error'] : null);
                    return;
                }

                var child_folders = response['items'];
                if (!child_folders) {
                    // 'directory does not exist' error.
                    onFailure();
                    return;
                }

                if (child_folders.length > 1) {
                    // 'runtime error' this should not happen
                    onFailure();
                    return;
                }

                get_id_for_relative_path(child_folders[0]['id'],
                    path_components);
            });
        };
        get_id_for_relative_path('root', path.split('/').reverse());
    }
 
 
    /**
     * Notebook Functions 
     */

    /**
     * Creates a new notebook file at the specified path, and
     * opens that notebook in a new window.
     *
     * @method scroll_to_cell
     * @param {String} path The path to create the new notebook at
     */
    ContentManager.prototype.new_notebook = function(path) {
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
            'api/notebooks',
            path
        );
        $.ajax(url,settings);
    };

    ContentManager.prototype.delete_notebook = function(name, path) {
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType : "json",
            success : $.proxy(this.events.trigger, this.events,
                'notebook_deleted.ContentManager',
                {
                    name: name,
                    path: path
                }),
            error : utils.log_ajax_error
        };
        var url = utils.url_join_encode(
            this.base_url,
            'api/notebooks',
            path,
            name
        );
        $.ajax(url, settings);
    };

    ContentManager.prototype.rename_notebook = function(path, name, new_name) {
        var that = this;
        var data = {name: new_name};
        var settings = {
            processData : false,
            cache : false,
            type : "PATCH",
            data : JSON.stringify(data),
            dataType: "json",
            headers : {'Content-Type': 'application/json'},
            success :  function (json, status, xhr) {
                that.events.trigger('notebook_rename_success.ContentManager',
                    json);
            },
            error : function (xhr, status, error) {
                that.events.trigger('notebook_rename_error.ContentManager',
                    [xhr, status, error]);
            }
        }
        var url = utils.url_join_encode(
            this.base_url,
            'api/notebooks',
            path,
            name
        );
        $.ajax(url, settings);
    };

    ContentManager.prototype.save_notebook = function(path, name, content,
        extra_settings) {
        var that = notebook;
        // Create a JSON model to be sent to the server.
        var model = {
            name : name,
            path : path,
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
            headers : {'Content-Type': 'application/json'},
            success : $.proxy(this.events.trigger, this.events,
                'notebook_save_success.ContentManager',
                $.extend(model, { start : start })),
            error : function (xhr, status, error) {
                that.events.trigger('notebook_save_error.ContentManager',
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
            'api/notebooks',
            path,
            name
        );
        $.ajax(url, settings);
    };

    /**
     * Checkpointing Functions 
     */

    ContentManager.prototype.save_checkpoint = function() {
        // This is not necessary - integrated into save
    };

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
    };

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
    ContentManager.prototype.list_contents = function(path, load_callback,
        error_callback) {
        var that = this;
        this.gapi_ready.done(function() {
            that.get_id_for_path(path, function(folder_id) {
                query = ('(fileExtension = \'ipynb\' or'
                    + ' mimeType = \'' + FOLDER_MIME_TYPE + '\')' 
                    + ' and \'' + folder_id + '\' in parents');
                var request = gapi.client.drive.files.list({
                    'maxResults' : 1000,
                    'q' : query
                });
                request.execute(function(response) {
                    // On a drive API error, call error_callback
                    if (!response || response['error']) {
                        error_callback(response ? response['error'] : null);
                        return;
                    }

                    // Convert this list to the format that is passed to
                    // load_callback.  Note that a files resource can represent
                    // a file or a directory.
                    // TODO: check that date formats are the same, and either
                    // convert to the IPython format, or document the difference.
                    var list = $.map(response['items'], function(files_resource) {
                        var type = files_resource['mimeType'] == FOLDER_MIME_TYPE ? 'directory' : 'notebook';
                        return {
                            type: type,
                            name: files_resource['title'],
                            path: path,
                            created: files_resource['createdDate'],
                            last_modified: files_resource['modifiedDate']
                        };
                    });
                    load_callback(list);
                });
            }, error_callback);
        });
    };


    IPython.ContentManager = ContentManager;

    return {'ContentManager': ContentManager};
}); 
