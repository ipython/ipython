// Test the widget manager.
casper.notebook_test(function () {
    var index;
    var slider = {};
    
    this.then(function () {
    
        // Check if the WidgetManager class is defined.
        this.test.assert(this.evaluate(function() {
            return IPython.WidgetManager !== undefined; 
        }), 'WidgetManager class is defined');

        // Check if the widget manager has been instantiated.
        this.test.assert(this.evaluate(function() {
            return IPython.notebook.kernel.widget_manager !== undefined; 
        }), 'Notebook widget manager instantiated');

        // Try creating a widget from Javascript.
        slider.id = this.evaluate(function() {
            var slider = IPython.notebook.kernel.widget_manager.create_model({
                 model_name: 'WidgetModel', 
                 widget_class: 'IPython.html.widgets.widget_int.IntSlider',
                 init_state_callback: function(model) { console.log('Create success!', model); }});
            return slider.id;
        });
    });

    index = this.append_cell(
        'from IPython.html.widgets import Widget\n' + 
        'widget = list(Widget.widgets.values())[0]\n' +
        'print(widget.model_id)');
    this.execute_cell_then(index, function(index) {
        var output = this.get_output_cell(index).text.trim();
        this.test.assertEquals(output, slider.id, "Widget created from the front-end.");
    });
});
