// Test the widget framework.
casper.notebook_test(function () {
    var index;
    
    this.then(function () {
    
        // Check if the WidgetManager class is defined.
        this.test.assert(this.evaluate(function() {
            return IPython.WidgetManager != undefined; 
        }), 'WidgetManager class is defined');
    });

    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    this.wait(500); // Wait for require.js async callbacks to load dependencies.

    this.then(function () {
        // Check if the widget manager has been instanciated.
        this.test.assert(this.evaluate(function() {
            return IPython.widget_manager != undefined; 
        }), 'Notebook widget manager instanciated');
    });

    index = this.append_cell(
        'names = [name for name in dir(widgets)' + 
        ' if name.endswith("Widget") and name!= "Widget" and name!= "DOMWidget"]\n' +
        'for name in names:\n' +
        '    print(name)\n');
    this.execute_cell_then(index, function(index){

        // Get the widget names that are registered with the widget manager.  Assume
        // a 1 to 1 mapping of model and widgets names (model names just have 'model'
        // suffixed).
        var javascript_names = this.evaluate(function () {
            names = [];
            for (var name in IPython.widget_manager._model_types) {
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
    
    throttle_index = this.append_cell(
        'import time\n' +
        'textbox = widgets.StringWidget()\n' +
        'display(textbox)\n'+
        'textbox.add_class("my-throttle-textbox")\n' +
        'def handle_change(name, old, new):\n' +
        '    print(len(new))\n' +
        '    time.sleep(0.5)\n' +
        'textbox.on_trait_change(handle_change)\n' +
        'print("Success")');
    this.execute_cell_then(throttle_index, function(index){
        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Test throttling cell executed with correct output');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.my-throttle-textbox'), 'Textbox exists.');

        // Send 20 characters
        this.sendKeys('.my-throttle-textbox', '....................');
    });

    this.wait(2000); // Wait for clicks to execute in kernel

    this.then(function(){
        var resume = true;
        var i = 0;
        while (resume) {
            i++;
            var output = this.get_output_cell(throttle_index, i);  
            if (output === undefined || output === null) {
                resume = false;
                i--;
            }
        }

        // Only 4 outputs should have printed, but because of timing, sometimes
        // 5 outputs will print.  All we need to do is verify num outputs <= 5
        // because that is much less than 20.
        this.test.assert(i <= 5, 'Messages throttled.');

        // We also need to verify that the last state sent was correct.
        var last_state = this.get_output_cell(throttle_index, i).text;
        this.test.assert(last_state == "20\n", "Last state sent when throttling.");
    })
});
