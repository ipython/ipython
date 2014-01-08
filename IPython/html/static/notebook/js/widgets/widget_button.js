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

define(["notebook/js/widgets/widget"], function(widget_manager){
    
    var ButtonWidgetModel = IPython.WidgetModel.extend({});
    widget_manager.register_widget_model('ButtonWidgetModel', ButtonWidgetModel);

    var ButtonView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            var that = this;
            this.setElement($("<button />")
                .addClass('btn'));

            this.update(); // Set defaults.
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            var description = this.model.get('description');
            description = description.replace(/ /g, '&nbsp;', 'm');
            description = description.replace(/\n/g, '<br>\n', 'm');
            if (description.length === 0) {
                this.$el.html('&nbsp;'); // Preserve button height
            } else {
                this.$el.html(description);
            }
            
            if (this.model.get('disabled')) {
                this.$el.attr('disabled','disabled');
            } else {
                this.$el.removeAttr('disabled');
            }

            return IPython.DOMWidgetView.prototype.update.call(this);
        },

        events: {
            'click': '_handle_click',
        },
        
        _handle_click: function(){
            this.send({event: 'click'});
        },
    });

    widget_manager.register_widget_view('ButtonView', ButtonView);

});
