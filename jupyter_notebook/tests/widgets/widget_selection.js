// Test selection class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var combo_selector = '.widget-area .widget-subarea .widget-hbox .btn-group .widget-combo-btn';
    var multibtn_selector = '.widget-area .widget-subarea .widget-hbox.widget-toggle-buttons .btn-group';
    var radio_selector = '.widget-area .widget-subarea .widget-hbox .widget-radio-box';
    var list_selector = '.widget-area .widget-subarea .widget-hbox .widget-listbox';

    var selection_index;
    var selection_values = 'abcd';
    var check_state = function(context, index, state){
        if (0 <= index && index < selection_values.length) {
            var multibtn_state = context.cell_element_function(selection_index, multibtn_selector + ' .btn:nth-child(' + (index + 1) + ')', 'hasClass', ['active']);
            var radio_state = context.cell_element_function(selection_index, radio_selector + ' .radio:nth-child(' + (index + 1) + ') input', 'prop', ['checked']);
            var list_val = context.cell_element_function(selection_index, list_selector, 'val');
            var combo_val = context.cell_element_function(selection_index, combo_selector, 'html');
            
            var val = selection_values.charAt(index);
            var list_state = (val == list_val);
            var combo_state = (val == combo_val);

            return multibtn_state == state &&
                radio_state == state &&
                list_state == state &&
                combo_state == state;
        }
        return true;
    };

    var verify_selection = function(context, index){
        for (var i = 0; i < selection_values.length; i++) {
            if (!check_state(context, i, i==index)) {
                return false;
            }
        }
        return true;
    };

//values=["' + selection_values + '"[i] for i in range(4)]
    selection_index = this.append_cell(
        'options=["' + selection_values + '"[i] for i in range(4)]\n' +
        'selection = [widgets.Dropdown(options=options),\n' +
        '    widgets.ToggleButtons(options=options),\n' +
        '    widgets.RadioButtons(options=options),\n' +
        '    widgets.Select(options=options)]\n' +
        '[display(selection[i]) for i in range(4)]\n' +
        'for widget in selection:\n' +
        '    def handle_change(name,old,new):\n' +
        '        for other_widget in selection:\n' +
        '            other_widget.value = new\n' +
        '    widget.on_trait_change(handle_change, "value")\n' +
        'print("Success")\n');
    this.execute_cell_then(selection_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create selection cell executed with correct output.');
    });

    // Wait for the widgets to actually display.
    this.wait_for_element(selection_index, combo_selector);
    this.wait_for_element(selection_index, multibtn_selector);
    this.wait_for_element(selection_index, radio_selector);
    this.wait_for_element(selection_index, list_selector);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(selection_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(selection_index, combo_selector),
             'Widget combobox exists.');

        this.test.assert(this.cell_element_exists(selection_index, multibtn_selector),
            'Widget multibutton exists.');

        this.test.assert(this.cell_element_exists(selection_index, radio_selector),
            'Widget radio buttons exists.');

        this.test.assert(this.cell_element_exists(selection_index, list_selector),
            'Widget list exists.');

        // Verify that no items are selected.
        this.test.assert(verify_selection(this, 0), 'Default first item selected.');
    });

    index = this.append_cell(
        'for widget in selection:\n' +
        '    widget.value = "a"\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Python select item executed with correct output.');

        // Verify that the first item is selected.
        this.test.assert(verify_selection(this, 0), 'Python selected');

        // Verify that selecting a radio button updates all of the others.
        this.cell_element_function(selection_index, radio_selector + ' .radio:nth-child(2) input', 'click');
    });
    this.wait_for_idle();
    this.then(function () {
        this.test.assert(verify_selection(this, 1), 'Radio button selection updated view states correctly.');

        // Verify that selecting a list option updates all of the others.
        this.cell_element_function(selection_index, list_selector + ' option:nth-child(3)', 'click');
    });
    this.wait_for_idle();
    this.then(function () {
        this.test.assert(verify_selection(this, 2), 'List selection updated view states correctly.');

        // Verify that selecting a multibutton option updates all of the others.
        // Bootstrap3 has changed the toggle button group behavior.  Two clicks
        // are required to actually select an item.
        this.cell_element_function(selection_index, multibtn_selector + ' .btn:nth-child(4)', 'click');
        this.cell_element_function(selection_index, multibtn_selector + ' .btn:nth-child(4)', 'click');
    });
    this.wait_for_idle();
    this.then(function () {
        this.test.assert(verify_selection(this, 3), 'Multibutton selection updated view states correctly.');

        // Verify that selecting a combobox option updates all of the others.
        this.cell_element_function(selection_index, '.widget-area .widget-subarea .widget-hbox .btn-group ul.dropdown-menu li:nth-child(3) a', 'click');
    });
    this.wait_for_idle();
    this.then(function () {
        this.test.assert(verify_selection(this, 2), 'Combobox selection updated view states correctly.');
    });

    this.wait_for_idle();

    index = this.append_cell(
        'from copy import copy\n' +
        'for widget in selection:\n' +
        '    d = copy(widget.options)\n' +
        '    d.append("z")\n' +
        '    widget.options = d\n' +
        'selection[0].value = "z"');
    this.execute_cell_then(index, function(index){

        // Verify that selecting a combobox option updates all of the others.
        this.test.assert(verify_selection(this, 4), 'Item added to selection widget.');
    });
});