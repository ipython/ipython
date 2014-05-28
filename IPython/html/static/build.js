({
    paths: {
        backbone    : "components/backbone/backbone",
        bootstrap   : "components/bootstrap/bootstrap/js/bootstrap.min",
        jquery      : "components/jquery/jquery.min",
        "jquery-ui" : "components/jquery-ui/ui/minified/jquery-ui.min",
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
    },

    baseUrl : "",
    name: "widgets/js/staticmanager",
    optimize: null
})
