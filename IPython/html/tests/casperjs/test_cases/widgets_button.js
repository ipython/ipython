// Test widget button class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

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
});