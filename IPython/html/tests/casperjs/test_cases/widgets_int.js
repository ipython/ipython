// Test widget int class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var int_text_query_2 = '.widget-area .widget-subarea .widget-hbox-single .my-second-int-text';

    var int_index = this.append_cell(
        'int_widget = widgets.IntTextWidget()\n' +
        'display(int_widget)\n' + 
        'int_widget.add_class("my-second-int-text")\n' + 
        'print("Success")\n');
    this.execute_cell_then(int_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create int cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, int_text_query_2),
            'Widget int textbox exists.');

        this.cell_element_function(int_index, int_text_query_2, 'val', ['']);
        this.sendKeys(int_text_query_2, '1.05');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', 
            'Int textbox value set.');
        this.cell_element_function(int_index, int_text_query_2, 'val', ['']);
        this.sendKeys(int_text_query_2, '123456789');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '123456789\n', 
            'Long int textbox value set (probably triggers throttling).');
        this.cell_element_function(int_index, int_text_query_2, 'val', ['']);
        this.sendKeys(int_text_query_2, '12hello');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '12\n', 
            'Invald int textbox value caught and filtered.');
    });
    
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var slider_query = '.widget-area .widget-subarea .widget-hbox-single .slider';
    var int_text_query = '.widget-area .widget-subarea .widget-hbox-single .my-second-num-test-text';

    var intrange_index = this.append_cell(
        'intrange = [widgets.BoundedIntTextWidget(),\n' +
        '    widgets.IntSliderWidget()]\n' +
        '[display(intrange[i]) for i in range(2)]\n' +
        'intrange[0].add_class("my-second-num-test-text")\n' +  
        'print("Success")\n');
    this.execute_cell_then(intrange_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
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
        'for widget in intrange:\n' +
        '    widget.max = 50\n' +
        '    widget.min = -50\n' +
        '    widget.value = 25\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
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

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', 
            'Int textbox set int range value');

        // Clear the int textbox value and then set it to 120 by emulating
        // keyboard presses.
        this.cell_element_function(intrange_index, int_text_query, 'val', ['']);
        this.sendKeys(int_text_query, '120');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '50\n', 
            'Int textbox value bound');

        // Clear the int textbox value and then set it to 'hello world' by 
        // emulating keyboard presses.  'hello world' should get filtered...
        this.cell_element_function(intrange_index, int_text_query, 'val', ['']);
        this.sendKeys(int_text_query, 'hello world');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '50\n', 
            'Invalid int textbox characters ignored');
    });    
});