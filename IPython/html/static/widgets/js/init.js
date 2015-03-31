// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/manager",
    "widgets/js/widget",
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
], function(widgetmanager, widget) {
    // Register all of the loaded models and views with the widget manager.
    for (var i = 2; i < arguments.length; i++) {
        var module = arguments[i];
        for (var target_name in module) {
            if (module.hasOwnProperty(target_name)) {
                var target = module[target_name];
                if (target.prototype instanceof widget.WidgetModel) {
                    widgetmanager.WidgetManager.register_widget_model(target_name, target);
                } else if (target.prototype instanceof widget.WidgetView) {
                    widgetmanager.WidgetManager.register_widget_view(target_name, target);
                }
            }
        }
    }
    return {'WidgetManager': widgetmanager.WidgetManager}; 
});
