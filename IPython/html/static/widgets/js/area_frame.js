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
        this.iframe[0].contentWindow.postMessage({
            'type': 'clear',
        }, '*');
    };

    return {
        'WidgetAreaFrame': WidgetAreaFrame,
    };
});
