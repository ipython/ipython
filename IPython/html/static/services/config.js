// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/utils',
    ],
function($, utils) {
    var ConfigSection = function(section_name, options) {
        this.section_name = section_name;
        this.base_url = options.base_url;
        this.data = {};
        
        var that = this;
        
        /* .loaded is a promise, fulfilled the first time the config is loaded
         * from the server. Code can do:
         *      conf.loaded.then(function() { ... using conf.data ... });
         */
        this._one_load_finished = false;
        this.loaded = new Promise(function(resolve, reject) {
            that._finish_firstload = resolve;
        });
    };

    ConfigSection.prototype.api_url = function() {
        return utils.url_join_encode(this.base_url, 'api/config', that.section_name);
    };
    
    ConfigSection.prototype._load_done = function() {
        if (!this._one_load_finished) {
            this._one_load_finished = true;
            this._finish_firstload();
        }
    };
    
    ConfigSection.prototype.load = function() {
        var p = new Promise(function(resolve, reject) {
            $.ajax(this.api_url(), {
                cache : false,
                type : "GET",
                dataType : "json",
                success: function(data, status, jqXHR) {
                    this.data = data;
                    this._load_done();
                    resolve(data);
                },
                error: function(jqXHR, status, error) {
                    // Should never happen; mark as loaded so things don't keep
                    // waiting.
                    this._load_done();
                    utils.log_ajax_error(jqXHR, status, error);
                    reject(utils.wrap_ajax_error(jqXHR, status, error));
                }
            });
        });
    };
    
    ConfigSection.prototype.update = function(newdata) {
        return new Promise(function(resolve, reject) {
            $.ajax(this.api_url(), {
                processData: false;
                type : "PATCH",
                data: JSON.stringify(newdata),
                dataType : "json",
                contentType: 'application/json',
                success: function(data, status, jqXHR) {
                    this.data = data;
                    this._load_done();
                    resolve(data);
                },
                error: function(jqXHR, status, error) {
                    utils.log_ajax_error(jqXHR, status, error);
                    reject(utils.wrap_ajax_error(jqXHR, status, error));
                }
            });
        });
    };

});
