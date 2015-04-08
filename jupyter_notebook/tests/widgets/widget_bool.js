// Test widget bool class
casper.notebook_test(function () {
    "use strict";

    // Create a checkbox and togglebutton.
    var bool_index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'bool_widgets = [widgets.Checkbox(description="Title", value=True),\n' +
        '    widgets.ToggleButton(description="Title", value=True)]\n' +
        'display(bool_widgets[0])\n' +
        'display(bool_widgets[1])\n' +
        'print("Success")');
    this.execute_cell_then(bool_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create bool widget cell executed with correct output.');
    });

    // Wait for the widgets to actually display.
    var widget_checkbox_selector = '.widget-area .widget-subarea .widget-hbox input';
    var widget_togglebutton_selector = '.widget-area .widget-subarea button';
    this.wait_for_element(bool_index, widget_checkbox_selector);
    this.wait_for_element(bool_index, widget_togglebutton_selector);

    // Continue the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(bool_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(bool_index, 
            widget_checkbox_selector),
            'Checkbox exists.');

        this.test.assert(this.cell_element_function(bool_index, 
            widget_checkbox_selector, 'prop', ['checked']),
            'Checkbox is checked.');

        this.test.assert(this.cell_element_exists(bool_index, 
            '.widget-area .widget-subarea .widget-hbox .widget-label'),
            'Checkbox label exists.');

        this.test.assert(this.cell_element_function(bool_index, 
            '.widget-area .widget-subarea .widget-hbox .widget-label', 'html')=="Title",
            'Checkbox labeled correctly.');

        this.test.assert(this.cell_element_exists(bool_index, 
            widget_togglebutton_selector),
            'Toggle button exists.');

        this.test.assert(this.cell_element_function(bool_index, 
            widget_togglebutton_selector, 'html')=='<i class="fa"></i>Title',
            'Toggle button labeled correctly.');

        this.test.assert(this.cell_element_function(bool_index, 
            widget_togglebutton_selector, 'hasClass', ['active']),
            'Toggle button is toggled.');
    });

    // Try changing the state of the widgets programatically.
    var index = this.append_cell(
        'bool_widgets[0].value = False\n' +
        'bool_widgets[1].value = False\n' +
        'print("Success")');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Change bool widget value cell executed with correct output.');

        this.test.assert(! this.cell_element_function(bool_index, 
            widget_checkbox_selector, 'prop', ['checked']),
            'Checkbox is not checked. (1)');

        this.test.assert(! this.cell_element_function(bool_index, 
            widget_togglebutton_selector, 'hasClass', ['active']),
            'Toggle button is not toggled. (1)');
 
        // Try toggling the bool by clicking on the checkbox.
        this.cell_element_function(bool_index, widget_checkbox_selector, 'click');

        this.test.assert(this.cell_element_function(bool_index, 
            widget_checkbox_selector, 'prop', ['checked']),
            'Checkbox is checked. (2)');

        // Try toggling the bool by clicking on the toggle button.
        this.cell_element_function(bool_index, widget_togglebutton_selector, 'click');

        this.test.assert(this.cell_element_function(bool_index, 
            widget_togglebutton_selector, 'hasClass', ['active']),
            'Toggle button is toggled. (3)');

    });
});
