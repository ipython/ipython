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
     * Name of newly created notebook files.
     * @type {string}
     */
    ContentManager.NEW_NOTEBOOK_TITLE = 'Untitled';

    /**
     * Extension for notebook files.
     * @type {string}
     */
    ContentManager.NOTEBOOK_EXTENSION = 'ipynb';


    ContentManager.MULTIPART_BOUNDARY = '-------314159265358979323846';

    ContentManager.NOTEBOOK_MIMETYPE = 'application/ipynb';


    /**
     * low level Google Drive functions
     *
     * NOTE: these functions should only be called after gapi_ready has been
     * resolved, with the excpetion of authorize(), and on_gapi_load() which
     * is private and should not be called at all.  Typical usage is:
     *
     * var that = this;
     * this.gapi_ready.done(function () {
     *     that.get_id_for_path(...)
     *     ...
     * });
     */

    /*
     * Load Google Drive client library
     * @private
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
     * @method get_id_for_path
     * @param {String} path The path
     * @param {Function} onSuccess called with the folder Id on success
     * @param {Function} onFailure called with the error on Failure
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
                + ' and title = \'' + this_component + '\''
                + ' and trashed = false');
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
     * Gets the Google Drive folder ID corresponding to a path.  Since
     * the Google Drive API doesn't expose a path structure, it is necessary
     * to manually walk the path from root.
     * @method get_id_for_path
     * @param {String} folder_id The google Drive folder id to search
     * @param {String} filename The filename to find in folder_id
     * @param {Function} onSuccess called with a files resource on success (see
     *     Google Drive API documentation for more information on the files
     *     resource).
     * @param {Function} onFailure called with the error on Failure
     */
    ContentManager.prototype.get_resource_for_filename = function(
        folder_id,
        filename,
        onSuccess,
        onFailure) {
        var query = ('title = \'' + filename + '\''
                + ' and \'' + folder_id + '\' in parents'
                + ' and trashed = false');
        var request = gapi.client.drive.files.list({
            'q': query
        });
        request.execute(function(response) {
            if (!response || response['error']) {
                onFailure(response ? response['error'] : null);
                return;
            }

            var files = response['items'];
            if (!files) {
                // 'directory does not exist' error.
                onFailure();
                return;
            }

            if (files.length > 1) {
                // 'runtime error' this should not happen
                onFailure();
                return;
            }

            onSuccess(files[0]);

        });
    };

    /**
    * Uploads a notebook to Drive, either creating a new one or saving an
    * existing one.
    *
    * @method upload_to_drive
    * @param {string} data The file contents as a string
    * @param {Object} metadata File metadata
    * @param {function(gapi.client.drive.files.Resource)} success_callback callback for
    *     success
    * @param {function(?):?} error_callback callback for error, takes response object
    * @param {string=} opt_fileId file Id.  If false, a new file is created.
    * @param {Object?} opt_params a dictionary containing the following keys
    *     pinned: whether this save should be pinned
    */
    ContentManager.prototype.upload_to_drive = function(data, metadata,
        success_callback, error_callback, opt_fileId, opt_params) {
        var params = opt_params || {};
        var delimiter = '\r\n--' + ContentManager.MULTIPART_BOUNDARY + '\r\n';
        var close_delim = '\r\n--' + ContentManager.MULTIPART_BOUNDARY + '--';
        var body = delimiter +
            'Content-Type: application/json\r\n\r\n' +
            JSON.stringify(metadata) +
            delimiter +
            'Content-Type: ' + ContentManager.NOTEBOOK_MIMETYPE + '\r\n' +
            '\r\n' +
            data +
            close_delim;

        var path = '/upload/drive/v2/files';
        var method = 'POST';
        if (opt_fileId) {
            path += '/' + opt_fileId;
            method = 'PUT';
        }

        var request = gapi.client.request({
            'path': path,
            'method': method,
            'params': {
                'uploadType': 'multipart',
                'pinned' : params['pinned']
            },
            'headers': {
                'Content-Type': 'multipart/mixed; boundary="' +
                ContentManager.MULTIPART_BOUNDARY + '"'
            },
            'body': body
        });
        request.execute(function(response) {
            if (!response || response['error']) {
                error_callback(response ? response['error'] : null);
                return;
            }

            success_callback(response);
        });
    };

    /**
     * Obtains the filename that should be used for a new file in a given folder.
     * This is the next file in the series Untitled0, Untitled1, ... in the given
     * drive folder.  As a fallback, returns Untitled.
     *
     * @method get_new_filename
     * @param {function(string)} callback Called with the name for the new file.
     * @param {string} opt_folderId optinal Drive folder Id to search for
     *     filenames.  Uses root, if none is specified.
     */
    ContentManager.prototype.get_new_filename = function(callback, opt_folderId) {
        /** @type {string} */
        var folderId = opt_folderId || 'root';
        var query = 'title contains \'' + ContentManager.NEW_NOTEBOOK_TITLE + '\'' +
            ' and \'' + folderId + '\' in parents' +
            ' and trashed = false';
        var request = gapi.client.drive.files.list({
            'maxResults': 1000,
            'folderId' : folderId,
            'q': query
        });

        request.execute(function(response) {
            // Use 'Untitled.ipynb' as a fallback in case of error
            var fallbackFilename = ContentManager.NEW_NOTEBOOK_TITLE + '.' +
            ContentManager.NOTEBOOK_EXTENSION;
            if (!response || response['error']) {
                callback(fallbackFilename);
                return;
            }

            var files = response['items'] || [];
            var existingFilenames = $.map(files, function(filesResource) {
                return filesResource['title'];
            });

            // Loop over file names Untitled0, ... , UntitledN where N is the number of
            // elements in existingFilenames.  Select the first file name that does not
            // belong to existingFilenames.  This is guaranteed to find a file name
            // that does not belong to existingFilenames, since there are N + 1 file
            // names tried, and existingFilenames contains N elements.
            for (var i = 0; i <= existingFilenames.length; i++) {
                /** @type {string} */
                var filename = ContentManager.NEW_NOTEBOOK_TITLE + i + '.' +
                    ContentManager.NOTEBOOK_EXTENSION;
                if (existingFilenames.indexOf(filename) == -1) {
                    callback(filename);
                    return;
                }
            }

            // Control should not reach this point, so an error has occured
            callback(fallbackFilename);
        });
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
    ContentManager.prototype.load_notebook = function (path, name, success_callback, 
        error_callback) {
        var that = this;
        this.gapi_ready.done(function() {
            that.get_id_for_path(path, function(folder_id) {
                that.get_resource_for_filename(folder_id, name, function(file_resource) {
                    // Sends request to load file to drive.
                    var token = gapi.auth.getToken()['access_token'];
                    var xhrRequest = new XMLHttpRequest();
                    xhrRequest.open('GET', file_resource['downloadUrl'], true);
                    xhrRequest.setRequestHeader('Authorization', 'Bearer ' + token);
                    xhrRequest.onreadystatechange = function(e) {
                        if (xhrRequest.readyState == 4) {
                            if (xhrRequest.status == 200) {
                                var notebook_contents = xhrRequest.responseText;
                                //colab.nbformat.convertJsonNotebookToRealtime(
                                //    notebook_contents, model);
                                var model = JSON.parse(notebook_contents);

                                success_callback({
                                    content: model,
                                    // A hack to deal with file/memory format conversions
                                    name: model.metadata.name
                                });
                            } else {
                                error_callback(xhrRequest);
                            }
                        }
                    };
                    xhrRequest.send();
                }, error_callback)
            }, error_callback);
        });
    };

    /**
     * Creates a new notebook file at the specified path, and
     * opens that notebook in a new window.
     *
     * @method scroll_to_cell
     * @param {String} path The path to create the new notebook at
     */
    ContentManager.prototype.new_notebook = function(path) {
        var that = this;
        this.gapi_ready.done(function() {
            that.get_id_for_path(path, function(folder_id) {
                that.get_new_filename(function(filename) {
                    var data = {
                        'worksheets': [{
                            'cells' : [{
                                'cell_type': 'code',
                                'input': '',
                                'outputs': [],
                                'language': 'python'
                            }],
                        }],
                        'metadata': {
                            'name': filename,
                        },
                        'nbformat': 3,
                        'nbformat_minor': 0
                    };
                    var metadata = {
                        'parents' : [{'id' : folder_id}],
                        'title' : filename,
                        'description': 'IP[y] file',
                        'mimeType': ContentManager.NOTEBOOK_MIMETYPE
                    }
                    that.upload_to_drive(JSON.stringify(data), metadata, function (data, status, xhr) {
                        var notebook_name = data.name;
                        window.open(
                            utils.url_join_encode(
                                that.base_url,
                                'contents',
                                path,
                                filename
                            ),
                            '_blank'
                        );
                    }, function(){});
                }, folder_id);
            })
        });
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
            'api/contents',
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
            'api/contents',
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
            'api/contents',
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

    ContentManager.prototype.list_checkpoints = function(notebook) {
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
    ContentManager.prototype.list_contents = function(path, load_callback,
        error_callback) {
        var that = this;
        this.gapi_ready.done(function() {
            that.get_id_for_path(path, function(folder_id) {
                query = ('(fileExtension = \'ipynb\' or'
                    + ' mimeType = \'' + FOLDER_MIME_TYPE + '\')' 
                    + ' and \'' + folder_id + '\' in parents'
                    + ' and trashed = false');
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
