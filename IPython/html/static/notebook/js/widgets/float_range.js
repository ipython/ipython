require(["notebook/js/widget"], function () {
    var FloatRangeWidgetModel = IPython.WidgetModel.extend({});
    IPython.notebook.widget_manager.register_widget_model('FloatRangeWidgetModel', FloatRangeWidgetModel);

    var FloatSliderView = IPython.WidgetView.extend({
        
        // Called when view is rendered.
        render : function(){
            this.$el
                .html('')
                .addClass(this.model.comm.comm_id);
            this.$slider = $('<div />')
                            .slider({})
                            .addClass('slider');
            
            // Put the slider in a container 
            this.$slider_container = $('<div />')
                                    .css('padding-top', '4px')
                                    .css('padding-bottom', '4px')
                                    .append(this.$slider);    
            this.$el.append(this.$slider_container);
            
            // Set defaults.
            this.update();
        },
        
        // Handles: Backend -> Frontend Sync
        //          Frontent -> Frontend Sync
        update : function(){
            // Slider related keys.
            var _keys = ['value', 'step', 'max', 'min', 'disabled', 'orientation'];
            for (var index in _keys) {
                var key = _keys[index];
                if (this.model.get(key) != undefined) {
                    this.$slider.slider("option", key, this.model.get(key));
                }
            }
        },
        
        // Handles: User input
        events: { "slide" : "handleSliderChange" }, 
        handleSliderChange: function(e, ui) { 
            this.model.set('value', ui.value); 
            this.model.apply(this);
        },
    });

    IPython.notebook.widget_manager.register_widget_view('FloatSliderView', FloatSliderView);


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
});