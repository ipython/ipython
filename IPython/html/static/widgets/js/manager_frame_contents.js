// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "widgets/js/init",
], function(widgetmanager) { 
    var widget_manager = null;
    
    // Register message listener.
    window.addEventListener('message', function(e){
        // Handle when a window message is recieved.
        
        // TODO: check e.origin AND e.source
        if (e.data.type == 'init') {
            widget_manager = new widgetmanager.WidgetManager(
                e.data.comm_manager, 
                e.data.get_msg_cell);
        }
    });
});
