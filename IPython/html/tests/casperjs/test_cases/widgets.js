// Test the widget framework.
casper.notebook_test(function () {
    var index;

    // Test widget dependencies ////////////////////////////////////////////////
    this.then(function () {
    
        // Check if the WidgetManager class is defined.
        this.test.assert(this.evaluate(function() {
            return IPython.WidgetManager != undefined; 
        }), 'WidgetManager class is defined');
    });

    index = append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    execute_cell_then(index);

    this.wait(500); // Wait for require.js async callbacks to load dependencies.

    this.then(function () {
        // Check if the widget manager has been instanciated.
        this.test.assert(this.evaluate(function() {
            return IPython.widget_manager != undefined; 
        }), 'Notebook widget manager instanciated');
    });


    // Check widget mapping ////////////////////////////////////////////////////
    index = append_cell(
        'names = [name for name in dir(widgets)' + 
        ' if name.endswith("Widget") and name!= "Widget"]\n' +
        'for name in names:\n' +
        '    print(name)\n');
    execute_cell_then(index, function(index){

        // Get the widget names that are registered with the widget manager.  Assume
        // a 1 to 1 mapping of model and widgets names (model names just have 'model'
        // suffixed).
        var javascript_names = this.evaluate(function () {
            names = [];
            for (var name in IPython.widget_manager.widget_model_types) {
                names.push(name.replace('Model',''));
            }
            return names;
        });

        // Get the widget names registered in python.
        var python_names = this.get_output_cell(index).text.split('\n');

        // Make sure the two lists have the same items.
        for (var i in javascript_names) {
            var javascript_name = javascript_names[i];
            var found = false;
            for (var j in python_names) {
                var python_name = python_names[j];
                if (python_name==javascript_name) {
                    found = true;
                    break;
                }
            }
            this.test.assert(found, javascript_name + ' exists in python');
        }
        for (var i in python_names) {
            var python_name = python_names[i];
            if (python_name.length > 0) {
                var found = false;
                for (var j in javascript_names) {
                    var javascript_name = javascript_names[j];
                    if (python_name==javascript_name) {
                        found = true;
                        break;
                    }
                }
                this.test.assert(found, python_name + ' exists in javascript');
            }
        }
    });


    // Test button widget //////////////////////////////////////////////////////
    var button_cell_index = append_cell(
        'button = widgets.ButtonWidget(description="Title")\n' +
        'display(button)\n'+
        'print("Success")\n' +
        'def handle_click(sender):\n' +
        '    print("Clicked")\n' +
        'button.on_click(handle_click)');
    execute_cell_then(button_cell_index, function(index){

        var button_output = this.get_output_cell(index).text;
        this.test.assert(button_output == 'Success\n', 
            'Create button widget, cell executed with correct output.');

        this.test.assert(cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Create button widget, widget subarea exist.');

        this.test.assert(cell_element_exists(index, 
            '.widget-area .widget-subarea button'),
            'Create button widget, widget button exist.');

        this.test.assert(cell_element_function(index, 
            '.widget-area .widget-subarea button', 'html')=='Title',
            'Set button description.');

        cell_element_function(index, 
            '.widget-area .widget-subarea button', 'click');
    });

    this.wait(500); // Wait for click to execute in kernel and write output

    this.then(function () {
        this.test.assert(this.get_output_cell(button_cell_index, 1).text == 'Clicked\n', 
            'Button click event fires.');
    });

    index = append_cell(
        'button.close()\n'+
        'print("Success")\n');
    execute_cell_then(index, function(index){

        var button_output = this.get_output_cell(index).text;
        this.test.assert(button_output == 'Success\n', 
            'Close button, cell executed with correct output.');

        this.test.assert(! cell_element_exists(button_cell_index, 
            '.widget-area .widget-subarea button'),
            'Remove button, widget button doesn\'t exist.');
    });
});

