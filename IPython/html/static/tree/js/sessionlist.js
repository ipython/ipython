// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
], function(IPython, $, utils) {
    "use strict";

    var SesssionList = function (options) {
        /**
         * Constructor
         *
         * Parameters:
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          events: $(Events) instance
         *          base_url : string
         */
        this.events = options.events;
        this.sessions = {};
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
    };
    
    SesssionList.prototype.load_sessions = function(){
        var that = this;
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(that.sessions_loaded, this),
            error : utils.log_ajax_error,
        };
        var url = utils.url_join_encode(this.base_url, 'api/sessions');
        $.ajax(url, settings);
    };

    SesssionList.prototype.sessions_loaded = function(data){
        this.sessions = {};
        var len = data.length;
        var nb_path;
        for (var i=0; i<len; i++) {
            nb_path = data[i].notebook.path;
            this.sessions[nb_path] = data[i].id;
        }
        this.events.trigger('sessions_loaded.Dashboard', this.sessions);
    };

    // Backwards compatability.
    IPython.SesssionList = SesssionList;

    return {'SesssionList': SesssionList};
});
