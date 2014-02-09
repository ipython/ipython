// Test widget int class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var int_text = {}
    int_text.query = '.widget-area .widget-subarea .widget-hbox-single .my-second-int-text';
    int_text.index = this.append_cell(
        'int_widget = widgets.IntTextWidget()\n' +
        'display(int_widget)\n' + 
        'int_widget.add_class("my-second-int-text")\n' + 
        'print(int_widget.model_id)\n');
    this.execute_cell_then(int_text.index, function(index){
        int_text.model_id = this.get_output_cell(index).text.trim();
        
        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, int_text.query),
            'Widget int textbox exists.');

        this.cell_element_function(int_text.index, int_text.query, 'val', ['']);
        this.sendKeys(int_text.query, '1.05');
    });

    this.wait_for_widget(int_text);

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', 
            'Int textbox value set.');
        this.cell_element_function(int_text.index, int_text.query, 'val', ['']);
        this.sendKeys(int_text.query, '123456789');
    });

    this.wait_for_widget(int_text);

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '123456789\n', 
            'Long int textbox value set (probably triggers throttling).');
        this.cell_element_function(int_text.index, int_text.query, 'val', ['']);
        this.sendKeys(int_text.query, '12hello');
    });

    this.wait_for_widget(int_text);

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
    var int_text2 = {};
    int_text2.query = '.widget-area .widget-subarea .widget-hbox-single .my-second-num-test-text';
    int_text2.index = this.append_cell(
        'intrange = [widgets.BoundedIntTextWidget(),\n' +
        '    widgets.IntSliderWidget()]\n' +
        '[display(intrange[i]) for i in range(2)]\n' +
        'intrange[0].add_class("my-second-num-test-text")\n' +  
        'print(intrange[0].model_id)\n');
    this.execute_cell_then(int_text2.index, function(index){
        int_text2.model_id = this.get_output_cell(index).text.trim();

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, slider_query),
            'Widget slider exists.');

        this.test.assert(this.cell_element_exists(index, int_text2.query),
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

        this.test.assert(this.cell_element_exists(int_text2.index, slider_query), 
            'Widget slider exists.');

        this.test.assert(this.cell_element_function(int_text2.index, slider_query, 
            'slider', ['value']) == 25,
            'Slider set to Python value.');

        this.test.assert(this.cell_element_function(int_text2.index, int_text2.query,
            'val') == 25, 'Int textbox set to Python value.');

        // Clear the int textbox value and then set it to 1 by emulating
        // keyboard presses.
        this.cell_element_function(int_text2.index, int_text2.query, 'val', ['']);
        this.sendKeys(int_text2.query, '1');
    });

    this.wait_for_widget(int_text2);

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', 
            'Int textbox set int range value');

        // Clear the int textbox value and then set it to 120 by emulating
        // keyboard presses.
        this.cell_element_function(int_text2.index, int_text2.query, 'val', ['']);
        this.sendKeys(int_text2.query, '120');
    });

    this.wait_for_widget(int_text2);

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '50\n', 
            'Int textbox value bound');

        // Clear the int textbox value and then set it to 'hello world' by 
        // emulating keyboard presses.  'hello world' should get filtered...
        this.cell_element_function(int_text2.index, int_text2.query, 'val', ['']);
        this.sendKeys(int_text2.query, 'hello world');
    });

    this.wait_for_widget(int_text2);

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '50\n', 
            'Invalid int textbox characters ignored');
    });    
});