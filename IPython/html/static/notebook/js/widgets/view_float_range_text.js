
var FloatTextView = IPython.WidgetView.extend({
    
    // Called when view is rendered.
    render : function(){
        this.$el
            .html('')
            .addClass(this.model.comm.comm_id);
        this.$textbox = $('<input type="text" />')
            .addClass('input')
            .appendTo(this.$el);
        this.update(); // Set defaults.
    },
    
    // Handles: Backend -> Frontend Sync
    //          Frontent -> Frontend Sync
    update : function(){
        var value = this.model.get('value');
        if (!this.changing && parseFloat(this.$textbox.val()) != value) {
            this.$textbox.val(value);
        }
        
        if (this.model.get('disabled')) {
            this.$textbox.attr('disabled','disabled');
        } else {
            this.$textbox.removeAttr('disabled');
        }
    },
    
    
    events: {"keyup input" : "handleChanging",
            "paste input" : "handleChanging",
            "cut input" : "handleChanging",
            "change input" : "handleChanged"}, // Fires only when control is validated or looses focus.
    
    // Handles and validates user input.
    handleChanging: function(e) { 
        
        // Try to parse value as a float.
        var numericalValue = 0.0;
        if (e.target.value != '') {
            numericalValue = parseFloat(e.target.value);
        }
        
        // If parse failed, reset value to value stored in model.
        if (isNaN(numericalValue)) {
            e.target.value = this.model.get('value');
        } else if (!isNaN(numericalValue)) {
            numericalValue = Math.min(this.model.get('max'), numericalValue);
            numericalValue = Math.max(this.model.get('min'), numericalValue);
            
            // Apply the value if it has changed.
            if (numericalValue != this.model.get('value')) {
                this.changing = true;
                this.model.set('value', numericalValue);
                this.model.apply(this);
                this.changing = false;
            }
        }
    },
    
    // Applies validated input.
    handleChanged: function(e) { 
        // Update the textbox
        if (this.model.get('value') != e.target.value) {
            e.target.value = this.model.get('value');
        }
    }
});

IPython.notebook.widget_manager.register_widget_view('FloatTextView', FloatTextView);
