// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'services/kernels/js/kernel',
], function(IPython, $, utils, kernel) {
    "use strict";

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
        this.events = options.events;
    };

    /**
     * GET /api/sessions
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
     */
    Session.prototype.start = function (success, error) {
        var that = this;
        var on_success = function (data, status, xhr) {
            console.log("Session started: ", data.id);
            var kernel_service_url = utils.url_path_join(that.base_url, "api/kernels");
            that.kernel = new kernel.Kernel(
                kernel_service_url, that.ws_url, that.notebook,
                that.kernel_model.id, that.kernel_model.name);
            that.kernel._kernel_started(data.kernel);
            if (success) {
                success(data, status, xhr);
            }
        };
        var on_error = function (xhr, status, err) {
            that.events.trigger('status_dead.Kernel');
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
     */
    Session.prototype.change = function (notebook_name, notebook_path, kernel_name, success, error) {
        this.notebook_model.name = notebook_name;
        this.notebook_model.path = notebook_path;
        this.kernel_model.name = kernel_name;

        $.ajax(this.session_url, {
            processData: false,
            cache: false,
            type: "PATCH",
            data: JSON.stringify(this._get_model()),
            dataType : "json",
            success: this._on_success(success),
            error: this._on_error(error)
        });
    };

    Session.prototype.rename_notebook = function (name, path, success, error) {
        this.change(name, path, this.kernel_model.name, success, error);
    };

    /**
     * DELETE /api/sessions/[:session_id]
     */
    Session.prototype.delete = function (success, error) {
        if (this.kernel) {
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
    
    Session.prototype._get_model = function () {
        return {
            notebook: this.notebook_model,
            kernel: this.kernel_model
        };
    };

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

    Session.prototype._on_success = function (success) {
        var that = this;
        return function (data, status, xhr) {
            that._update_model(data);
            if (success) {
                success(data, status, xhr);
            }
        };
    };

    Session.prototype._on_error = function (error) {
        return function (xhr, status, err) {
            utils.log_ajax_error(xhr, status, err);
            if (error) {
                error(xhr, status, err);
            }
        };
    };


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
