// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

/// <reference path="./jquery.d.ts" />
/// <reference path="./promise.d.ts" />
import $ = require("jquery");
var utils;
// import utils = require('../base/js/utils');

export class ConfigSection {   
    public section_name;
    public base_url;
    public data;
    public loaded;

    private _one_load_finished;
    private _finish_firstload;

    constructor(section_name, options) {
        this.section_name = section_name;
        this.base_url = options.base_url;
        this.data = {};
        
        /* .loaded is a promise, fulfilled the first time the config is loaded
         * from the server. Code can do:
         *      conf.loaded.then(function() { ... using conf.data ... });
         */
        this._one_load_finished = false;
        this.loaded = new Promise((resolve, reject) => {
            this._finish_firstload = resolve;
        });
    }

    api_url() {
        return utils.url_join_encode(this.base_url, 'api/config', this.section_name);
    }

    _load_done() {
        if (!this._one_load_finished) {
            this._one_load_finished = true;
            this._finish_firstload();
        }
    }

    load() {
        return utils.promising_ajax(this.api_url(), {
            cache: false,
            type: "GET",
            dataType: "json",
        }).then(data => {
            this.data = data;
            this._load_done();
            return data;
        });
    }

    /**
     * Modify the config values stored. Update the local data immediately,
     * send the change to the server, and use the updated data from the server
     * when the reply comes.
     */
    update(newdata) {
        $.extend(true, this.data, newdata);  // true -> recursive update
        
        return utils.promising_ajax(this.api_url(), {
            processData: false,
            type : "PATCH",
            data: JSON.stringify(newdata),
            dataType : "json",
            contentType: 'application/json',
        }).then(data => {
            this.data = data;
            this._load_done();
            return data;
        });
    }
};

export class ConfigWithDefaults {
    public section;
    public defaults;
    public classname;

    constructor(section, defaults, classname) {
        this.section = section;
        this.defaults = defaults;
        this.classname = classname;
    }

    _class_data() {
        if (this.classname) {
            return this.section.data[this.classname] || {};
        } else {
            return this.section.data
        }
    }

    /**
     * Wait for config to have loaded, then get a value or the default.
     * Returns a promise.
     */
    get(key) {
        return this.section.loaded.then(() => {
            return this._class_data()[key] || this.defaults[key]
        });
    }

    /**
     * Return a config value. If config is not yet loaded, return the default
     * instead of waiting for it to load.
     */
    get_sync(key) {
        return this._class_data()[key] || this.defaults[key];
    }

    /**
     * Set a config value. Send the update to the server, and change our
     * local copy of the data immediately.
     * Returns a promise which is fulfilled when the server replies to the
     * change.
     */
     set(key, value) {
         var d = {};
         d[key] = value;
         if (this.classname) {
            var d2 = {};
            d2[this.classname] = d;
            return this.section.update(d2);
        } else {
            return this.section.update(d);
        }
    }
}
