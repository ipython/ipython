// Test widget float class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var float_text_query_2 = '.widget-area .widget-subarea .widget-hbox-single .my-second-float-text';

    var float_index = this.append_cell(
        'float_widget = widgets.FloatTextWidget()\n' +
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
});