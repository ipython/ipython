// Test widget button class
casper.notebook_test(function () {
    var button_index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'button = widgets.Button(description="Title")\n' +
        'display(button)\n' +
        'print("Success")\n' +
        'def handle_click(sender):\n' +
        '    display("Clicked")\n' +
        'button.on_click(handle_click)');
    this.execute_cell_then(button_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n',
            'Create button cell executed with correct output.');
    });

    // Wait for the widgets to actually display.
    var widget_button_selector = '.widget-area .widget-subarea button';
    this.wait_for_element(button_index, widget_button_selector);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(button_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(button_index, 
            widget_button_selector),
            'Widget button exists.');

        this.test.assert(this.cell_element_function(button_index, 
            widget_button_selector, 'html')=='<i class="fa"></i>Title',
            'Set button description.');

        this.cell_element_function(button_index, 
            widget_button_selector, 'click');
    });

    this.wait_for_output(button_index, 1);

    this.then(function () {
        var warning_text = this.get_output_cell(button_index, 1).text;
        this.test.assertNotEquals(warning_text.indexOf('Warning'), -1,
            'Importing widgets show a warning');
        this.test.assertEquals(this.get_output_cell(button_index, 2).data['text/plain'], "'Clicked'",
            'Button click event fires.');
    });
});
