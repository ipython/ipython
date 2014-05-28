// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

// Setup require module.  Used when the staticmanager is reference by a webpage
// using something like <script src="">.  This require non-sense is ignored in
// the case that the static widget manager is "built" using the r.js optimizer.
require.config({
    // TODO: Replace rawgit with permanent url.
    baseUrl: 'https://rawgit.com/jdfreder/ipython/widgetpersistance/IPython/html/static/',

    paths: {
        underscore : 'https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.6.0/underscore-min',
        backbone : 'https://cdnjs.cloudflare.com/ajax/libs/backbone.js/1.1.2/backbone-min',
        "jquery-ui" : 'https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.4/jquery-ui.min',
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


// Define some global functions that can be called by the rest of the document
// while the manager is loading.  These functions are temporary and will be 
// replaced once the dependencies listed below are loaded by require.js.
var IPython = {};
IPython.widgets = {};
IPython.widgets._widget_cache = [];
IPython.widgets._widget_state_cache = [];
IPython.widgets._widget_display_cache = [];
IPython.widgets.create_widget = function(model_id, target) {
    IPython.widgets._widget_cache.push(arguments);
};
IPython.widgets.set_widget = function(model_id, state) {
    IPython.widgets._widget_state_cache.push(arguments);
};
IPython.widgets.display_widget = function(model_id, elementid) {
    IPython.widgets._widget_display_cache.push(arguments);
};


// Asynchronously load the manager.  When the manager is loaded, process all of
// the widgets that were queued for later.
require([
    "widgets/js/manager",
    "widgets/js/init",
    "jquery-ui",
], function(WidgetManager){ 
    IPython.widget_manager = new WidgetManager(undefined);

    IPython.widgets.create_widget = function(model_id, target) {
        IPython.widget_manager.get_model(model_id, target);
    };

    IPython.widgets.set_widget = function(model_id, state) {
        // Set the state as disabled since a comm doesn't exist for this
        // model at this point.
        var model = IPython.widget_manager.get_model(model_id);
        model.set_state($.extend(state, {disabled: true}));
    };

    IPython.widgets.display_widget = function(model_id, elementid) {
        // Displays a view for a particular model.
        var model = IPython.widget_manager.get_model(model_id);
        var view = IPython.widget_manager.create_view(model, {cell: elementid});
        if (view === null) {
            console.error("View creation failed", model);
        } else {
            $('#' + elementid).append(view.$el);
            IPython.widget_manager._handle_display_view(view);
        }
    };

    // Process caches.
    for (var i = 0; i < IPython.widgets._widget_cache.length; i++) {
        IPython.widgets.create_widget.apply(undefined, IPython.widgets._widget_cache[i]);
    }
    for (var i = 0; i < IPython.widgets._widget_state_cache.length; i++) {
        IPython.widgets.set_widget.apply(undefined, IPython.widgets._widget_state_cache[i]);
    }
    for (var i = 0; i < IPython.widgets._widget_display_cache.length; i++) {
        IPython.widgets.display_widget.apply(undefined, IPython.widgets._widget_display_cache[i]);
    }
});
