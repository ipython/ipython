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

define(["widgets/js/widget"], function(WidgetManager){

    var HTMLView = IPython.DOMWidgetView.extend({  
        render : function(){
            // Called when view is rendered.
            this.update(); // Set defaults.
        },
        
        update : function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            this.$el.html(this.model.get('value')); // CAUTION! .html(...) CALL MANDITORY!!!
            return HTMLView.__super__.update.apply(this);
        },
    });
    WidgetManager.register_widget_view('HTMLView', HTMLView);


    var LatexView = IPython.DOMWidgetView.extend({  
        render : function(){
            // Called when view is rendered.
            this.update(); // Set defaults.
        },
        
        update : function(){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            this.$el.text(this.model.get('value'));
            MathJax.Hub.Queue(["Typeset",MathJax.Hub,this.$el.get(0)]);

            return LatexView.__super__.update.apply(this);
        }, 
    });
    WidgetManager.register_widget_view('LatexView', LatexView);


    var TextareaView = IPython.DOMWidgetView.extend({  
        render: function(){
            // Called when view is rendered.
            this.$el
                .addClass('widget-hbox');
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
            // Handle when a custom msg is recieved from the back-end.
            if (content.method == "scroll_to_bottom") {
                this.scroll_to_bottom();                
            }
        },

        scroll_to_bottom: function (){
            // Scroll the text-area view to the bottom.
            this.$textbox.scrollTop(this.$textbox[0].scrollHeight);
        },

        update: function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                this.$textbox.val(this.model.get('value'));

                var disabled = this.model.get('disabled');
                this.$textbox.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text(description);
                    this.$label.show();
                }
            }
            return TextareaView.__super__.update.apply(this);
        },
        
        events: {
            // Dictionary of events and their handlers.
            "keyup textarea" : "handleChanging",
            "paste textarea" : "handleChanging",
            "cut textarea"   : "handleChanging"
        },
        
        handleChanging: function(e) { 
            // Handles and validates user input.
            
            // Calling model.set will trigger all of the other views of the 
            // model to update.
            this.model.set('value', e.target.value, {updated_view: this});
            this.touch();
        },
    });
    WidgetManager.register_widget_view('TextareaView', TextareaView);


    var TextView = IPython.DOMWidgetView.extend({  
        render: function(){
            // Called when view is rendered.
            this.$el
                .addClass('widget-hbox-single');
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
        
        update: function(options){
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            if (options === undefined || options.updated_view != this) {
                if (this.$textbox.val() != this.model.get('value')) {
                    this.$textbox.val(this.model.get('value'));
                }

                var disabled = this.model.get('disabled');
                this.$textbox.prop('disabled', disabled);

                var description = this.model.get('description');
                if (description.length === 0) {
                    this.$label.hide();
                } else {
                    this.$label.text(description);
                    this.$label.show();
                }
            }
            return TextView.__super__.update.apply(this);
        },
        
        events: {
            // Dictionary of events and their handlers.
            "keyup input"    : "handleChanging",
            "paste input"    : "handleChanging",
            "cut input"      : "handleChanging",
            "keypress input" : "handleKeypress",
            "blur input" : "handleBlur",
            "focusout input" : "handleFocusOut"
        },
        
        handleChanging: function(e) { 
            // Handles user input.

            // Calling model.set will trigger all of the other views of the 
            // model to update.
            this.model.set('value', e.target.value, {updated_view: this});
            this.touch();
        },
        
        handleKeypress: function(e) { 
            // Handles text submition
            if (e.keyCode == 13) { // Return key
                this.send({event: 'submit'});
                event.stopPropagation();
                event.preventDefault();
                return false;
            }
        },

        handleBlur: function(e) { 
            // Prevent a blur from firing if the blur was not user intended.
            // This is a workaround for the return-key focus loss bug.
            // TODO: Is the original bug actually a fault of the keyboard
            // manager?
            if (e.relatedTarget === null) {
                event.stopPropagation();
                event.preventDefault();
                return false;
            }
        },

        handleFocusOut: function(e) { 
            // Prevent a blur from firing if the blur was not user intended.
            // This is a workaround for the return-key focus loss bug.
            if (e.relatedTarget === null) {
                event.stopPropagation();
                event.preventDefault();
                return false;
            }
        },
    });
    WidgetManager.register_widget_view('TextView', TextView);
});
