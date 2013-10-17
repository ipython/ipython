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
