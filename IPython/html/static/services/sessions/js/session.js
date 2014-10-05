// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'services/kernels/js/kernel',
], function(IPython, $, utils, kernel) {
    "use strict";

    /**
     * Session object for accessing the session REST api. The session
     * should be used to start kernels and then shut them down -- for
     * all other operations, the kernel object should be used.
     *
     * Options should include:
     *  - notebook_name: the notebook name
     *  - notebook_path: the path (not including name) to the notebook
     *  - kernel_name: the type of kernel (e.g. python3)
     *  - base_url: the root url of the notebook server
     *  - ws_url: the url to access websockets
     *  - notebook: Notebook object
     *
     * @class Session
     * @param {Object} options
     */
    var Session = function (options) {
        this.id = null;
        this.notebook_model = {
            name: options.notebook_name,
            path: options.notebook_path
        };
        this.kernel_model = {
            id: null,
            name: options.kernel_name
        };

        this.base_url = options.base_url;
        this.ws_url = options.ws_url;
        this.session_service_url = utils.url_join_encode(this.base_url, 'api/sessions');
        this.session_url = null;

        this.notebook = options.notebook;
        this.kernel = null;
        this.events = options.notebook.events;

        this.bind_events();
    };

    Session.prototype.bind_events = function () {
        var that = this;
        var record_status = function (evt) {
            console.log('Session: ' + evt.type + ' (' + that.id + ')');
        };

        this.events.on('kernel_started.Session', record_status);
        this.events.on('kernel_dead.Session', record_status);
        this.events.on('status_killed.Session', record_status);
    };


    // Public REST api functions

    /**
     * GET /api/sessions
     *
     * Get a list of the current sessions.
     *
     * @function list
     * @param {function} [success] - function executed on ajax success
     * @param {function} [error] - functon executed on ajax error
     */
    Session.prototype.list = function (success, error) {
        $.ajax(this.session_service_url, {
            processData: false,
            cache: false,
            type: "GET",
            dataType: "json",
            success: success,
            error: this._on_error(error)
        });
    };

    /**
     * POST /api/sessions
     *
     * Start a new session. This function can only executed once.
     *
     * @function start
     * @param {function} [success] - function executed on ajax success
     * @param {function} [error] - functon executed on ajax error
     */
    Session.prototype.start = function (success, error) {
        var that = this;
        var on_success = function (data, status, xhr) {
            if (!that.kernel) {
                var kernel_service_url = utils.url_path_join(that.base_url, "api/kernels");
                that.kernel = new kernel.Kernel(kernel_service_url, that.ws_url, that.notebook, that.kernel_model.name);
            }
            that.events.trigger('kernel_started.Session', {session: that, kernel: that.kernel});
            that.kernel._kernel_started(data.kernel);
            if (success) {
                success(data, status, xhr);
            }
        };
        var on_error = function (xhr, status, err) {
            that.events.trigger('kernel_dead.Session', {session: that});
            if (error) {
                error(xhr, status, err);
            }
        };

        $.ajax(this.session_service_url, {
            processData: false,
            cache: false,
            type: "POST",
            data: JSON.stringify(this._get_model()),
            dataType: "json",
            success: this._on_success(on_success),
            error: this._on_error(on_error)
        });
    };

    /**
     * GET /api/sessions/[:session_id]
     *
     * Get information about a session.
     *
     * @function get_info
     * @param {function} [success] - function executed on ajax success
     * @param {function} [error] - functon executed on ajax error
     */
    Session.prototype.get_info = function (success, error) {
        $.ajax(this.session_url, {
            processData: false,
            cache: false,
            type: "GET",
            dataType: "json",
            success: this._on_success(success),
            error: this._on_error(error)
        });
    };

    /**
     * PATCH /api/sessions/[:session_id]
     *
     * Rename or move a notebook. If the given name or path are
     * undefined, then they will not be changed.
     *
     * @function rename_notebook
     * @param {string} [name] - new notebook name
     * @param {string} [path] - new path to notebook
     * @param {function} [success] - function executed on ajax success
     * @param {function} [error] - functon executed on ajax error
     */
    Session.prototype.rename_notebook = function (name, path, success, error) {
        if (name !== undefined) {
            this.notebook_model.name = name;
        }
        if (path !== undefined) {
            this.notebook_model.path = path;
        }

        $.ajax(this.session_url, {
            processData: false,
            cache: false,
            type: "PATCH",
            data: JSON.stringify(this._get_model()),
            dataType: "json",
            success: this._on_success(success),
            error: this._on_error(error)
        });
    };

    /**
     * DELETE /api/sessions/[:session_id]
     *
     * Kill the kernel and shutdown the session.
     *
     * @function delete
     * @param {function} [success] - function executed on ajax success
     * @param {function} [error] - functon executed on ajax error
     */
    Session.prototype.delete = function (success, error) {
        if (this.kernel) {
            this.events.trigger('status_killed.Session', {session: this, kernel: this.kernel});
            this.kernel._kernel_dead();
        }

        $.ajax(this.session_url, {
            processData: false,
            cache: false,
            type: "DELETE",
            dataType: "json",
            success: this._on_success(success),
            error: this._on_error(error)
        });
    };

    Session.prototype.restart = function (options, success, error) {
        var that = this;
        var start = function () {
            if (options && options.notebook_name) {
                that.notebook_model.name = options.notebook_name;
            }
            if (options && options.notebook_path) {
                that.notebook_model.path = options.notebook_path;
            }
            if (options && options.kernel_name) {
                that.kernel_model.name = options.kernel_name;
            }
            that.kernel_model.id = null;
            that.start(success, error);
        };
        this.delete(start, start);
    };

    // Helper functions

    /**
     * Get the data model for the session, which includes the notebook
     * (name and path) and kernel (name and id).
     *
     * @function _get_model
     * @returns {Object} - the data model
     */
    Session.prototype._get_model = function () {
        return {
            notebook: this.notebook_model,
            kernel: this.kernel_model
        };
    };

    /**
     * Update the data model from the given JSON object, which should
     * have attributes of `id`, `notebook`, and/or `kernel`. If
     * provided, the notebook data must include name and path, and the
     * kernel data must include name and id.
     *
     * @function _update_model
     * @param {Object} data - updated data model
     */
    Session.prototype._update_model = function (data) {
        if (data && data.id) {
            this.id = data.id;
            this.session_url = utils.url_join_encode(this.session_service_url, this.id);
        }
        if (data && data.notebook) {
            this.notebook_model.name = data.notebook.name;
            this.notebook_model.path = data.notebook.path;
        }
        if (data && data.kernel) {
            this.kernel_model.name = data.kernel.name;
            this.kernel_model.id = data.kernel.id;
        }
    };

    /**
     * Handle a successful AJAX request by updating the session data
     * model with the response, and then optionally calling a provided
     * callback.
     *
     * @function _on_success
     * @param {function} success - callback
     */
    Session.prototype._on_success = function (success) {
        var that = this;
        return function (data, status, xhr) {
            that._update_model(data);
            if (success) {
                success(data, status, xhr);
            }
        };
    };

    /**
     * Handle a failed AJAX request by logging the error message, and
     * then optionally calling a provided callback.
     *
     * @function _on_error
     * @param {function} error - callback
     */
    Session.prototype._on_error = function (error) {
        return function (xhr, status, err) {
            utils.log_ajax_error(xhr, status, err);
            if (error) {
                error(xhr, status, err);
            }
        };
    };

    /**
     * Error type indicating that the session is already starting.
     */
    var SessionAlreadyStarting = function (message) {
        this.name = "SessionAlreadyStarting";
        this.message = (message || "");
    };
    SessionAlreadyStarting.prototype = Error.prototype;
    
    // For backwards compatability.
    IPython.Session = Session;

    return {
        Session: Session,
        SessionAlreadyStarting: SessionAlreadyStarting
    };
});
