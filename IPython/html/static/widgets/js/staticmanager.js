// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

console.log('!!!loaded!');

require.config({
    // TODO: Replace rawgit with permanent url.
    baseUrl: 'https://rawgit.com/jdfreder/ipython/widgetpersistance/IPython/html/static/',

    paths: {
        underscore : 'https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.6.0/underscore-min',
        backbone : 'https://cdnjs.cloudflare.com/ajax/libs/backbone.js/1.1.2/backbone-min',
    },
    
    shim: {
        underscore: {
            exports: '_'
        },
        backbone: {
            deps: ["underscore", "jquery"],
            exports: "Backbone"
        }
    }
});

var IPython = {};
require([
    "widgets/js/manager",
    "widgets/js/init"
], function(WidgetManager){ 

    console.log('!!!required!');
});
