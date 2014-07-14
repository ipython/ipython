// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
], function($){
    var WidgetManagerFrame = function() {
        this.$el = $('<iframe src="/widgetmanager"></iframe>');
    };

    WidgetManagerFrame.prototype.init = function(comm_manager, notebook) {
        // TODO: Set * to the known origin.
        this.$el[0].contentWindow.postMessage({
            'type': 'init',
            'comm_manager': 2, //comm_manager,
            'get_msg_cell': 2 //$.proxy(notebook.get_msg_cell, notebook),
        }, '*');
    };

    return {'WidgetManagerFrame': WidgetManagerFrame};
});
