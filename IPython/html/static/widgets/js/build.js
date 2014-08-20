// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.
//
// Widget build file for r.js.
//
// This file can be used in conjuncture with r.js to build a single Javascript
// file containing all of the widget code, static widget manager, and 

({
    baseUrl : "../../",
    name: "widgets/js/staticmanager",
    out: "staticwidgets.min.js",
    
    paths: {
        backbone    : "components/backbone/backbone",
        bootstrap   : "components/bootstrap/js/bootstrap.min",
        jquery      : "components/jquery/jquery.min",
        jqueryui    : "components/jquery-ui/ui/minified/jquery-ui.min",
        underscore  : "components/underscore/underscore"
    },

    shim : {
        backbone : {
            deps : ["jquery", "underscore"],
            exports : "Backbone"
        },
        bootstrap : {
            deps : ["jquery"]
        },
        underscore : {
            exports : "_"
        }
    }
})
