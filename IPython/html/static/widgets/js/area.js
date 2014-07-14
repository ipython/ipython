// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    "jquery",
], function($){

    var WidgetArea = function (){
        // Constructor

        // Register message listener.
        window.addEventListener('message', $.proxy(this._handle_msg, this));

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

    WidgetArea.prototype._handle_msg = function(e) {
        // Handle when a window message is recieved.
        
        // TODO: check e.origin AND e.source
        if (e.data.type == 'display') {
            this.widget_area.show();
            var view = e.data.view;
            this.widget_subarea.append(view.$el);
        } else if (e.data.type == 'clear_output') {
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
