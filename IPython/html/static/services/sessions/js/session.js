// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'services/kernels/js/kernel',
], function(IPython, $, utils, kernel) {
    "use strict";

    var Session = function(options){
        this.kernel = null;
        this.id = null;
        this.notebook = options.notebook;
        this.events = options.notebook.events;
        this.name = options.notebook_name;
        this.path = options.notebook_path;
        this.kernel_name = options.kernel_name;
        this.base_url = options.base_url;
        this.ws_url = options.ws_url;
    };
    
    Session.prototype.start = function (success, error) {
        var that = this;
        var model = {
            notebook : {
                name : this.name,
                path : this.path
            },
            kernel : {
                name : this.kernel_name
            }
        };
        var settings = {
            processData : false,
            cache : false,
            type : "POST",
            data: JSON.stringify(model),
            dataType : "json",
            success : function (data, status, xhr) {
                that._handle_start_success(data);
                if (success) {
                    success(data, status, xhr);
                }
            },
            error : function (xhr, status, err) {
                that._handle_start_failure(xhr, status, err);
                if (error !== undefined) {
                    error(xhr, status, err);
                }
                utils.log_ajax_error(xhr, status, err);
            }
        };
        var url = utils.url_join_encode(this.base_url, 'api/sessions');
        $.ajax(url, settings);
    };
    
    Session.prototype.rename_notebook = function (name, path) {
        this.name = name;
        this.path = path;
        var model = {
            notebook : {
                name : this.name,
                path : this.path
            }
        };
        var settings = {
            processData : false,
            cache : false,
            type : "PATCH",
            data: JSON.stringify(model),
            dataType : "json",
            error : utils.log_ajax_error,
        };
        var url = utils.url_join_encode(this.base_url, 'api/sessions', this.id);
        $.ajax(url, settings);
    };
    
    Session.prototype.delete = function (success, error) {
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType : "json",
            success : success,
            error : error || utils.log_ajax_error,
        };
        if (this.kernel) {
            this.kernel.running = false;
            this.kernel.stop_channels();
        }
        var url = utils.url_join_encode(this.base_url, 'api/sessions', this.id);
        $.ajax(url, settings);
    };
    
    // Kernel related things
    /**
     * Create the Kernel object associated with this Session.
     * 
     * @method _handle_start_success
     */
    Session.prototype._handle_start_success = function (data, status, xhr) {
        this.id = data.id;
        // If we asked for 'python', the response will have 'python3' or 'python2'.
        this.kernel_name = data.kernel.name;
        this.events.trigger('started.Session', this);
        var kernel_service_url = utils.url_path_join(this.base_url, "api/kernels");
        this.kernel = new kernel.Kernel(kernel_service_url, this.ws_url, this.notebook, this.kernel_name);
        this.kernel._kernel_started(data.kernel);
    };

    Session.prototype._handle_start_failure = function (xhr, status, error) {
        this.events.trigger('start_failed.Session', [this, xhr, status, error]);
        this.events.trigger('status_dead.Kernel');
    };
    
    /**
     * Prompt the user to restart the IPython kernel.
     * 
     * @method restart_kernel
     */
    Session.prototype.restart_kernel = function () {
        this.kernel.restart();
    };
    
    Session.prototype.interrupt_kernel = function() {
        this.kernel.interrupt();
    };
    

    Session.prototype.kill_kernel = function() {
        this.kernel.kill();
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
        SessionAlreadyStarting: SessionAlreadyStarting,
    };
});
