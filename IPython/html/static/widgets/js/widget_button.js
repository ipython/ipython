//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// ButtonWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["widgets/js/widget"], function(WidgetManager){

    var ButtonView = IPython.DOMWidgetView.extend({
        render : function(){
            // Called when view is rendered.
            this.setElement($("<button />")
                .addClass('btn'));

            this.update(); // Set defaults.
        },
        
        update : function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            var description = this.model.get('description');
            if (description.length === 0) {
                this.$el.html("&nbsp;"); // Preserve button height
            } else {
                this.$el.text(description);
            }
            
            if (this.model.get('disabled')) {
                this.$el.attr('disabled','disabled');
            } else {
                this.$el.removeAttr('disabled');
            }

            return ButtonView.__super__.update.apply(this);
        },

        events: {
            // Dictionary of events and their handlers.
            'click': '_handle_click',
        },
        
        _handle_click: function(){
            // Handles when the button is clicked.
            this.send({event: 'click'});
        },
    });
    WidgetManager.register_widget_view('ButtonView', ButtonView);
});
