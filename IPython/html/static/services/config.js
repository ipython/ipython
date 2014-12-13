// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/utils',
    ],
function($, utils) {
    "use strict";
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
        return utils.url_join_encode(this.base_url, 'api/config', this.section_name);
    };
    
    ConfigSection.prototype._load_done = function() {
        if (!this._one_load_finished) {
            this._one_load_finished = true;
            this._finish_firstload();
        }
    };
    
    ConfigSection.prototype.load = function() {
        var that = this;
        return utils.promising_ajax(this.api_url(), {
            cache: false,
            type: "GET",
            dataType: "json",
        }).then(function(data) {
            that.data = data;
            that._load_done();
            return data;
        });
    };
    
    ConfigSection.prototype.update = function(newdata) {
        var that = this;
        return utils.promising_ajax(this.api_url(), {
            processData: false,
            type : "PATCH",
            data: JSON.stringify(newdata),
            dataType : "json",
            contentType: 'application/json',
        }).then(function(data) {
            that.data = data;
            that._load_done();
            return data;
        });
    };
    
    
    var ConfigWithDefaults = function(section, defaults, classname) {
        this.section = section;
        this.defaults = defaults;
        this.classname = classname;
    };
    
    ConfigWithDefaults.prototype._class_data = function() {
        if (this.classname) {
            return this.section.data[this.classname] || {};
        } else {
            return this.section.data
        }
    };
    
    /**
     * Wait for config to have loaded, then get a value or the default.
     * Returns a promise.
     */
    ConfigWithDefaults.prototype.get = function(key) {
        var that = this;
        return this.section.loaded.then(function() {
            return this._class_data()[key] || this.defaults[key]
        });
    };
    
    /**
     * Return a config value. If config is not yet loaded, return the default
     * instead of waiting for it to load.
     */
    ConfigWithDefaults.prototype.get_sync = function(key) {
        return this._class_data()[key] || this.defaults[key];
    };
    
    return {ConfigSection: ConfigSection,
            ConfigWithDefaults: ConfigWithDefaults,
           };

});
