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
        this.name = options.notebook_name;
        this.path = options.notebook_path;
        this.kernel_name = options.kernel_name;
        this.base_url = options.base_url;
    };
    
    Session.prototype.start = function(callback) {
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
                if (callback) {
                    callback(data, status, xhr);
                }
            },
            error : utils.log_ajax_error,
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
    
    Session.prototype.delete = function() {
        var settings = {
            processData : false,
            cache : false,
            type : "DELETE",
            dataType : "json",
            error : utils.log_ajax_error,
        };
        this.kernel.running = false;
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
        var kernel_service_url = utils.url_path_join(this.base_url, "api/kernels");
        this.kernel = new kernel.Kernel(kernel_service_url, this.notebook, this.kernel_name);
        this.kernel._kernel_started(data.kernel);
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
    
    // For backwards compatability.
    IPython.Session = Session;

    return {'Session': Session};
});
