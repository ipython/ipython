// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/manager",
    "widgets/js/widget_link",
    "widgets/js/widget_bool",
    "widgets/js/widget_button",
    "widgets/js/widget_box",
    "widgets/js/widget_float",
    "widgets/js/widget_image",
    "widgets/js/widget_int",
    "widgets/js/widget_output",
    "widgets/js/widget_selection",
    "widgets/js/widget_selectioncontainer",
    "widgets/js/widget_string",
], function(widgetmanager) {


    /**
     * From https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/endsWith
     * Can be removed with the string endsWith function is implemented in major browsers
     */
    var endsWith = function(target, searchString, position) {
        var subjectString = target.toString();
        if (position === undefined || position > subjectString.length) {
            position = subjectString.length;
        }
        position -= searchString.length;
        var lastIndex = subjectString.indexOf(searchString, position);
        return lastIndex !== -1 && lastIndex === position;
    };

    // Register all of the loaded models and views with the widget manager.
    for (var i = 1; i < arguments.length; i++) {
        var module = arguments[i];
        for (var target_name in module) {
            if (module.hasOwnProperty(target_name)) {
                if (endsWith(target_name, "View")) {
                    widgetmanager.WidgetManager.register_widget_view(target_name, module[target_name]);
                } else if (endsWith(target_name, "Model")) {
                    widgetmanager.WidgetManager.register_widget_model(target_name, module[target_name]);
                }
            }
        }
    }

    return {'WidgetManager': widgetmanager.WidgetManager}; 
});
