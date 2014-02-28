//----------------------------------------------------------------------------
//  Copyright (C) 2014  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Running Kernels List
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;
        
    var SesssionList = function (options) {
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
            success : $.proxy(that.sessions_loaded, this)
        };
        var url = utils.url_join_encode(this.base_url, 'api/sessions');
        $.ajax(url, settings);
    };

    SesssionList.prototype.sessions_loaded = function(data){
        this.sessions = {};
        var len = data.length;
        var nb_path;
        for (var i=0; i<len; i++) {
            nb_path = utils.url_path_join(
                data[i].notebook.path,
                data[i].notebook.name
            );
            this.sessions[nb_path] = data[i].id;
        }
        $([IPython.events]).trigger('sessions_loaded.Dashboard', this.sessions);
    };
    IPython.SesssionList = SesssionList;

    return IPython;

}(IPython));
