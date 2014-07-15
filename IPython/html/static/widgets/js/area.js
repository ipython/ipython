// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "jquery",
    "base/js/frame"
], function($, frame){

    var WidgetArea = function (){
        // Constructor

        // Register message listener.
        this.communicator = new frame.FrameCommunicator(parent);
        this.communicator.on_msg($.proxy(this._handle_msg, this));

        // Create widget area.
        var widget_area = $('<div/>')
            .addClass('widget-area')
            .hide();
        this.widget_area = widget_area;
        var widget_prompt = $('<div/>')
            .addClass('prompt')
            .appendTo(widget_area);
        var widget_subarea = $('<div/>')
            .addClass('widget-subarea')
            .appendTo(widget_area);
        this.widget_subarea = widget_subarea;
        var widget_clear_buton = $('<button />')
            .addClass('close')
            .html('&times;')
            .click(function() {
                widget_area.slideUp('', function(){ widget_subarea.html(''); });
                })
            .appendTo(widget_prompt);
        $('body').append(widget_area);
    };

    WidgetArea.prototype.display_view = function(view) {
        this.widget_area.show();
        this.widget_subarea.append(view.$el);
    };

    WidgetArea.prototype._handle_msg = function(msg, respond) {
        // Handle when a window message is recieved.
        
        if (msg.type == 'clear_output') {
            this.widget_subarea.html('');
            this.widget_subarea.height('');
            this.widget_area.height('');
            this.widget_area.hide();
        }
    };

    return {
        'WidgetArea': WidgetArea,
    };
});
