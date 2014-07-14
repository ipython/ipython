// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
], function($){

    var WidgetAreaFrame = function() {
        this.$el = $('<iframe src="/widgetarea"></iframe>');
    };

    WidgetAreaFrame.prototype.clear = function() {
        // TODO: Set * to the known origin.
        this.$el[0].contentWindow.postMessage({
            'type': 'clear',
        }, '*');
    };

    WidgetAreaFrame.prototype.display = function(view) {
        // TODO: Set * to the known origin.
        this.$el[0].contentWindow.postMessage({
            'type': 'display',
            'view': 'view'
        }, '*');
    };

    return {
        'WidgetAreaFrame': WidgetAreaFrame,
    };
});
