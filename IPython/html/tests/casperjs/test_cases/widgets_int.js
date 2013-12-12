// Test widget int class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var int_text_query_2 = '.widget-area .widget-subarea .widget-hbox-single .my-second-int-text';

    var int_index = this.append_cell(
        'int_widget = widgets.IntWidget()\n' +
        'display(int_widget)\n' + 
        'int_widget.add_class("my-second-int-text")\n' + 
        'print("Success")\n');
    this.execute_cell_then(int_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
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
        this.test.assert(this.get_output_cell(index).text == '1\n', 
            'Int textbox value set.');
        this.cell_element_function(int_index, int_text_query_2, 'val', ['']);
        this.sendKeys(int_text_query_2, '123456789');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '123456789\n', 
            'Long int textbox value set (probably triggers throttling).');
        this.cell_element_function(int_index, int_text_query_2, 'val', ['']);
        this.sendKeys(int_text_query_2, '12hello');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '12\n', 
            'Invald int textbox value caught and filtered.');
    });
});