// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "jquery",
], function($){
    var WidgetManagerFrame = function() {
        this.$el = $('<iframe src="/widgetmanager"></iframe>');
    };

    WidgetAreaFrame.prototype.init = function(comm_manager, notebook) {
        // TODO: Set * to the known origin.
        this.$el[0].contentWindow.postMessage({
            'type': 'init',
            'comm_manager': comm_manager,
            'get_msg_cell': $.proxy(e.data.notebook.get_msg_cell, e.data.notebook),
        }, '*');
    };

    return {'WidgetManagerFrame': WidgetManagerFrame};
});
