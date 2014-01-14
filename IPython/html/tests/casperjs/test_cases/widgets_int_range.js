// Test int range class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var slider_query = '.widget-area .widget-subarea .widget-hbox-single .slider';
    var int_text_query = '.widget-area .widget-subarea .widget-hbox-single .my-second-num-test-text';

    var intrange_index = this.append_cell(
        'intrange = widgets.IntRangeWidget()\n' +
        'display(intrange, view_name="IntTextView")\n' +
        'intrange.add_class("my-second-num-test-text")\n' +  
        'display(intrange)\n' + 
        'print("Success")\n');
    this.execute_cell_then(intrange_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create int range cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, slider_query),
            'Widget slider exists.');

        this.test.assert(this.cell_element_exists(index, int_text_query),
            'Widget int textbox exists.');
    });

    index = this.append_cell(
        'intrange.max = 50\n' +
        'intrange.min = -50\n' +
        'intrange.value = 25\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Int range properties cell executed with correct output.');

        this.test.assert(this.cell_element_exists(intrange_index, slider_query), 
            'Widget slider exists.');

        this.test.assert(this.cell_element_function(intrange_index, slider_query, 
            'slider', ['value']) == 25,
            'Slider set to Python value.');

        this.test.assert(this.cell_element_function(intrange_index, int_text_query,
            'val') == 25, 'Int textbox set to Python value.');

        // Clear the int textbox value and then set it to 1 by emulating
        // keyboard presses.
        this.cell_element_function(intrange_index, int_text_query, 'val', ['']);
        this.sendKeys(int_text_query, '1');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(intrange.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '1\n', 
            'Int textbox set int range value');

        // Clear the int textbox value and then set it to 120 by emulating
        // keyboard presses.
        this.cell_element_function(intrange_index, int_text_query, 'val', ['']);
        this.sendKeys(int_text_query, '120');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(intrange.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '50\n', 
            'Int textbox value bound');

        // Clear the int textbox value and then set it to 'hello world' by 
        // emulating keyboard presses.  'hello world' should get filtered...
        this.cell_element_function(intrange_index, int_text_query, 'val', ['']);
        this.sendKeys(int_text_query, 'hello world');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(intrange.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '50\n', 
            'Invalid int textbox characters ignored');
    });    
});