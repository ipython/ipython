// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/manager",
    "widgets/js/widget_bool",
    "widgets/js/widget_button",
    "widgets/js/widget_box",
    "widgets/js/widget_float",
    "widgets/js/widget_image",
    "widgets/js/widget_int",
    "widgets/js/widget_selection",
    "widgets/js/widget_selectioncontainer",
    "widgets/js/widget_string",
], function(widgetmanager) { 

    // Register all of the loaded views with the widget manager.
    for (var i = 1; i < arguments.length; i++) {
        for (var target_name in arguments[i]) {
            if (arguments[i].hasOwnProperty(target_name)) {
                widgetmanager.WidgetManager.register_widget_view(target_name, arguments[i][target_name]);
            }
        }
    }

    return {'WidgetManager': widgetmanager.WidgetManager}; 
});
