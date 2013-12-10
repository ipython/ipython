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

    // Close the button widget asynchronisly.
    index = this.append_cell('button.close()\n');
    this.execute_cell(index);

    this.wait(500); // Wait for the button to close.

    this.then(function(){
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

    // Test float range widget /////////////////////////////////////////////////
    var slider_query = '.widget-area .widget-subarea .widget-hbox-single .slider';
    var float_text_query = '.widget-area .widget-subarea .widget-hbox-single .widget-numeric-text';

    var floatrange_index = this.append_cell(
        'floatrange = widgets.FloatRangeWidget()\n' +
        'display(floatrange)\n' + 
        'display(floatrange, view_name="FloatTextView")\n' + 
        'print("Success")\n');
    this.execute_cell_then(floatrange_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create float range cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, slider_query),
            'Widget slider exists.');

        this.test.assert(this.cell_element_exists(index, float_text_query),
            'Widget float textbox exists.');
    });

    index = this.append_cell(
        'floatrange.max = 50.0\n' +
        'floatrange.min = -50.0\n' +
        'floatrange.value = 25.0\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Float range properties cell executed with correct output.');

        this.test.assert(this.cell_element_exists(floatrange_index, slider_query), 
            'Widget slider exists.');

        this.test.assert(this.cell_element_function(floatrange_index, slider_query, 
            'slider', ['value']) == 25.0,
            'Slider set to Python value.');

        this.test.assert(this.cell_element_function(floatrange_index, float_text_query,
            'val') == 25.0, 'Float textbox set to Python value.');

        // Clear the float textbox value and then set it to 1 by emulating
        // keyboard presses.
        this.cell_element_function(floatrange_index, float_text_query, 'val', ['']);
        this.sendKeys(float_text_query, '1');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(floatrange.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '1.0\n', 
            'Float textbox set float range value');

        // Clear the float textbox value and then set it to 120 by emulating
        // keyboard presses.
        this.cell_element_function(floatrange_index, float_text_query, 'val', ['']);
        this.sendKeys(float_text_query, '120');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(floatrange.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '50.0\n', 
            'Float textbox value bound');

        // Clear the float textbox value and then set it to 'hello world' by 
        // emulating keyboard presses.  'hello world' should get filtered...
        this.cell_element_function(floatrange_index, float_text_query, 'val', ['']);
        this.sendKeys(float_text_query, 'hello world');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(floatrange.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '50.0\n', 
            'Invalid float textbox characters ignored');
    });

    // Test float widget ///////////////////////////////////////////////////////
    var float_text_query_2 = '.widget-area .widget-subarea .widget-hbox-single .my-second-float-text';

    var float_index = this.append_cell(
        'float_widget = widgets.FloatWidget()\n' +
        'display(float_widget)\n' + 
        'float_widget.add_class("my-second-float-text")\n' + 
        'print("Success")\n');
    this.execute_cell_then(float_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create float cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, float_text_query_2),
            'Widget float textbox exists.');

        this.cell_element_function(float_index, float_text_query_2, 'val', ['']);
        this.sendKeys(float_text_query_2, '1.05');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(float_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '1.05\n', 
            'Float textbox value set.');
        this.cell_element_function(float_index, float_text_query_2, 'val', ['']);
        this.sendKeys(float_text_query_2, '123456789.0');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(float_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '123456789.0\n', 
            'Long float textbox value set (probably triggers throttling).');
        this.cell_element_function(float_index, float_text_query_2, 'val', ['']);
        this.sendKeys(float_text_query_2, '12hello');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(float_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '12.0\n', 
            'Invald float textbox value caught and filtered.');
    });

    // Test image widget ///////////////////////////////////////////////////////

    // Get the temporary directory that the test server is running in.
    var cwd = '';
    index = this.append_cell('!echo $(pwd)');
    this.execute_cell_then(index, function(index){
        cwd = this.get_output_cell(index).text.trim();
    });

    test_jpg = '/9j/4AAQSkZJRgABAQEASABIAAD//gATQ3JlYXRlZCB3aXRoIEdJTVD/2wBDACAWGBwYFCAcGhwkIiAmMFA0MCwsMGJGSjpQdGZ6eHJmcG6AkLicgIiuim5woNqirr7EztDOfJri8uDI8LjKzsb/2wBDASIkJDAqMF40NF7GhHCExsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsbGxsb/wgARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAAA//EABUBAQEAAAAAAAAAAAAAAAAAAAME/9oADAMBAAIQAxAAAAECv//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Bf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEABj8Cf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8hf//aAAwDAQACAAMAAAAQn//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Qf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Qf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8Qf//Z';
    test_results = '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDi6KKK+ZP3EKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA//Z';

    var image_index = this.append_cell(
        'import base64\n' + 
        'data = base64.b64decode("' + test_jpg + '")\n' +
        'image = widgets.ImageWidget()\n' +
        'image.image_format = "jpeg"\n' +
        'image.value = data\n' +
        'image.width = "50px"\n' +
        'image.height = "50px"\n' +
        // Set css that will make the image render within the PhantomJS visible
        // window.  If we don't do this, the captured image will be black.
        'image.set_css({"background": "blue", "z-index": "9999", "position": "fixed", "top": "0px", "left": "0px"})\n' + 
        'display(image)\n' + 
        'image.add_class("my-test-image")\n' + 
        'print("Success")\n');
    this.execute_cell_then(image_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create image executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea img'),
            'Image exists.');

        // Capture a screenshot of the img element as a base64 string.
        var fs = require('fs');
        capture_filename = cwd + fs.separator + 'captured.jpg';
        this.captureSelector(capture_filename, '.my-test-image');
        var stream = fs.open(capture_filename, 'rb');
        var captured = btoa(stream.read());
        stream.close()
        fs.remove(capture_filename);

        // Uncomment line below to output captured image data to a text file.
        // fs.write('./captured.txt', captured, 'w');

        this.test.assert(test_results==captured, "Red image data displayed correctly.");
    });

});


