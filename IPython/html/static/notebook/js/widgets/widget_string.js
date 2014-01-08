//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// StringWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widgets/widget"], function(widget_manager){
    var StringWidgetModel = IPython.WidgetModel.extend({});
    widget_manager.register_widget_model('StringWidgetModel', StringWidgetModel);

    var HTMLView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.update(); // Set defaults.
        },
        
        update : function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            this.$el.html(this.model.get('value'));
            return IPython.DOMWidgetView.prototype.update.call(this);
        },
        
    });

    widget_manager.register_widget_view('HTMLView', HTMLView);


    var LatexView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render : function(){
            this.update(); // Set defaults.
        },
        
        update : function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            this.$el.html(this.model.get('value'));
            MathJax.Hub.Queue(["Typeset",MathJax.Hub,this.$el.get(0)]);

            return IPython.DOMWidgetView.prototype.update.call(this);
        },
        
    });

    widget_manager.register_widget_view('LatexView', LatexView);

    var TextAreaView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render: function(){
            this.$el
                .addClass('widget-hbox')
                .html('');
            this.$label = $('<div />')
                .appendTo(this.$el)
                .addClass('widget-hlabel')
                .hide();
            this.$textbox = $('<textarea />')
                .attr('rows', 5)
                .addClass('widget-text')
                .appendTo(this.$el);
            this.$el_to_style = this.$textbox; // Set default element to style
            this.update(); // Set defaults.

            this.model.on('msg:custom', $.proxy(this._handle_textarea_msg, this));
        },


        _handle_textarea_msg: function (content){
            if (content.method == "scroll_to_bottom") {
                this.scroll_to_bottom();                
            }
        },


        scroll_to_bottom: function (){
            this.$textbox.scrollTop(this.$textbox[0].scrollHeight);
        },

        
        update: function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (!this.user_invoked_update) {
                this.$textbox.val(this.model.get('value'));
            }

            var disabled = this.model.get('disabled');
            this.$textbox.prop('disabled', disabled);

            var description = this.model.get('description');
            if (description.length === 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.DOMWidgetView.prototype.update.call(this);
        },
        
        events: {"keyup textarea": "handleChanging",
                "paste textarea": "handleChanging",
                "cut textarea": "handleChanging"},
        
        // Handles and validates user input.
        handleChanging: function(e) { 
            this.user_invoked_update = true;
            this.model.set('value', e.target.value);
            this.touch();
            this.user_invoked_update = false;
        },
    });

    widget_manager.register_widget_view('TextAreaView', TextAreaView);

    var TextBoxView = IPython.DOMWidgetView.extend({
      
        // Called when view is rendered.
        render: function(){
            this.$el
                .addClass('widget-hbox-single')
                .html('');
            this.$label = $('<div />')
                .addClass('widget-hlabel')
                .appendTo(this.$el)
                .hide();
            this.$textbox = $('<input type="text" />')
                .addClass('input')
                .addClass('widget-text')
                .appendTo(this.$el);
            this.$el_to_style = this.$textbox; // Set default element to style
            this.update(); // Set defaults.
        },
        
        update: function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (this.$textbox.val() != this.model.get('value')) {
                this.$textbox.val(this.model.get('value'));
            }

            var disabled = this.model.get('disabled');
            this.$textbox.prop('disabled', disabled);

            var description = this.model.get('description');
            if (description.length === 0) {
                this.$label.hide();
            } else {
                this.$label.html(description);
                this.$label.show();
            }
            return IPython.DOMWidgetView.prototype.update.call(this);
        },
        
        events: {"keyup input": "handleChanging",
                "paste input": "handleChanging",
                "cut input": "handleChanging",
                "keypress input": "handleKeypress"},
        
        // Handles and validates user input.
        handleChanging: function(e) { 
            this.model.set('value', e.target.value);
            this.touch();
        },
        
        // Handles text submition
        handleKeypress: function(e) { 
            if (e.keyCode == 13) { // Return key
                this.send({event: 'submit'});
            }
        },
    });

    widget_manager.register_widget_view('TextBoxView', TextBoxView);
});
