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


    // Check widget mapping ////////////////////////////////////////////////////
    index = this.append_cell(
        'names = [name for name in dir(widgets)' + 
        ' if name.endswith("Widget") and name!= "Widget"]\n' +
        'for name in names:\n' +
        '    print(name)\n');
    this.execute_cell_then(index, function(index){

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


    // Test bool widget ////////////////////////////////////////////////////////
    var bool_index = this.append_cell(
        'bool_widget = widgets.BoolWidget(description="Title", value=True)\n' +
        'display(bool_widget)\n'+
        'display(bool_widget, view_name="ToggleButtonView")\n' +
        'print("Success")');
    this.execute_cell_then(bool_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create bool widget cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-hbox-single input'),
            'Checkbox exists.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox-single input', 'prop', ['checked']),
            'Checkbox is checked.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-hbox-single .widget-hlabel'),
            'Checkbox label exists.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox-single .widget-hlabel', 'html')=="Title",
            'Checkbox labeled correctly.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea div button'),
            'Toggle button exists.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea div button', 'html')=="Title",
            'Toggle button labeled correctly.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea div button', 'hasClass', ['active']),
            'Toggle button is toggled.');

    });

    index = this.append_cell(
        'bool_widget.value = False\n' +
        'print("Success")');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Change bool widget value cell executed with correct output.');

        this.test.assert(! this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea .widget-hbox-single input', 'prop', ['checked']),
            'Checkbox is not checked. (1)');

        this.test.assert(! this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea div button', 'hasClass', ['active']),
            'Toggle button is not toggled. (1)');

        // Try toggling the bool by clicking on the toggle button.
        this.cell_element_function(bool_index, '.widget-area .widget-subarea div button', 'click');

        this.test.assert(this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea .widget-hbox-single input', 'prop', ['checked']),
            'Checkbox is checked. (2)');

        this.test.assert(this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea div button', 'hasClass', ['active']),
            'Toggle button is toggled. (2)');
 
        // Try toggling the bool by clicking on the checkbox.
        this.cell_element_function(bool_index, '.widget-area .widget-subarea .widget-hbox-single input', 'click');

        this.test.assert(! this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea .widget-hbox-single input', 'prop', ['checked']),
            'Checkbox is not checked. (3)');

        this.test.assert(! this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea div button', 'hasClass', ['active']),
            'Toggle button is not toggled. (3)');

    });

    // Test button widget //////////////////////////////////////////////////////
    var button_index = this.append_cell(
        'button = widgets.ButtonWidget(description="Title")\n' +
        'display(button)\n'+
        'print("Success")\n' +
        'def handle_click(sender):\n' +
        '    print("Clicked")\n' +
        'button.on_click(handle_click)');
    this.execute_cell_then(button_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create button cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea button'),
            'Widget button exists.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea button', 'html')=='Title',
            'Set button description.');

        this.cell_element_function(index, 
            '.widget-area .widget-subarea button', 'click');
    });

    this.wait(500); // Wait for click to execute in kernel and write output

    this.then(function () {
        this.test.assert(this.get_output_cell(button_index, 1).text == 'Clicked\n', 
            'Button click event fires.');
    });

    index = this.append_cell(
        'button.close()\n'+
        'print("Success")');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Close button cell executed with correct output.');

        this.test.assert(! this.cell_element_exists(button_index, 
            '.widget-area .widget-subarea button'),
            'Widget button doesn\'t exists.');
    });

    // Test container widget ///////////////////////////////////////////////////
    var container_index = this.append_cell(
        'container = widgets.ContainerWidget()\n' +
        'button = widgets.ButtonWidget(parent=container)\n'+
        'display(container)\n'+
        'container.add_class("my-test-class")\n'+
        'print("Success")\n');
    this.execute_cell_then(container_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create container cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-container'),
            'Widget container exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .my-test-class'),
            'add_class works.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .my-test-class button'),
            'Container parent/child relationship works.');
    });

    index = this.append_cell(
        'container.set_css("display", "none")\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Set container class CSS cell executed with correct output.');

        this.test.assert(this.cell_element_function(container_index, 
            '.widget-area .widget-subarea .my-test-class', 'css', ['display'])=='none',
            'set_css works.');
    });

    index = this.append_cell(
        'container.remove_class("my-test-class")\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Remove container class cell executed with correct output.');

        this.test.assert(! this.cell_element_exists(container_index, 
            '.widget-area .widget-subarea .my-test-class'),
            'remove_class works.');
    });

    index = this.append_cell(
        'display(button)\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Display container child executed with correct output.');

        this.test.assert(! this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-container'),
            'Parent container not displayed.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea button'),
            'Child displayed.');
    });
});

