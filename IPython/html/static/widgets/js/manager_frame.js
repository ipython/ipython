// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
    "base/js/frame"
], function($, frame){
    var WidgetManagerFrame = function(container) {
        this.$el = $('<iframe />')
            .attr('src', '/widgetmanager')
            .attr('name', 'widgetmanager');
        this.communicator = new frame.FrameCommunicator(this.$el, true);
    };

    WidgetManagerFrame.prototype.init = function(comm_manager, notebook) {
        this.communicator.msg({
            'type': 'init',
            'comm_manager': 2, //comm_manager,
            'get_msg_cell': 2 //$.proxy(notebook.get_msg_cell, notebook),
        });
    };

    return {'WidgetManagerFrame': WidgetManagerFrame};
});
