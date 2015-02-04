// Test the widget manager.
casper.notebook_test(function () {
    var index;
    
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
        this.evaluate(function() {
            IPython.notebook.kernel.widget_manager.create_model({
                model_name: 'WidgetModel', 
                widget_class: 'IPython.html.widgets.widget_int.IntSlider'})
                .then(function(model) { 
                    console.log('Create success!', model); 
                    window.slider_id = model.id; 
                }, function(error) { console.log(error); });
        });
    });

    // Wait for the state to be recieved.
    this.waitFor(function check() {
        return this.evaluate(function() {
            return window.slider_id !== undefined;
        });
    });

    index = this.append_cell(
        'from IPython.html.widgets import Widget\n' + 
        'widget = list(Widget.widgets.values())[0]\n' +
        'print(widget.model_id)');
    this.execute_cell_then(index, function(index) {
        var output = this.get_output_cell(index).text.trim();
        var slider_id = this.evaluate(function() { return window.slider_id; });
        this.test.assertEquals(output, slider_id, "Widget created from the front-end.");
    });

    // Widget persistence tests.
    index = this.append_cell(
        'from IPython.html.widgets import HTML\n' + 
        'from IPython.display import display\n' + 
        'display(HTML(value="<div id=\'hello\'></div>"))');
    this.execute_cell_then(index, function() {});

    index = this.append_cell(
        'display(HTML(value="<div id=\'world\'></div>"))');
    this.execute_cell_then(index, function() {});

    var that = this;
    this.then(function() {
        // Wait for the widgets to be shown.
        that.waitForSelector('#hello', function() {
            that.waitForSelector('#world', function() {
                that.test.assertExists('#hello', 'Hello HTML widget constructed.');
                that.test.assertExists('#world', 'World HTML widget constructed.');

                // Save the notebook.
                that.evaluate(function() {
                    IPython.notebook.save_notebook(false).then(function() {
                        window.was_saved = true;
                    });
                });
                that.waitFor(function check() {
                    return that.evaluate(function() {
                        return window.was_saved;
                    });
                }, function then() {

                    // Reload the page
                    that.reload(function() {

                        // Wait for the elements to show up again.
                        that.waitForSelector('#hello', function() {
                            that.waitForSelector('#world', function() {
                                that.test.assertExists('#hello', 'Hello HTML widget persisted.');
                                that.test.assertExists('#world', 'World HTML widget persisted.');
                            });
                        });
                    });
                });
            });
        });
    });

    
});
