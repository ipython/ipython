// Test multicontainer class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    // Test tab view
    var multicontainer1_query = '.widget-area .widget-subarea div div.nav-tabs';
    var multicontainer1_index = this.append_cell(
        'multicontainer = widgets.Tab()\n' +
        'page1 = widgets.Text()\n' +
        'page2 = widgets.Text()\n' +
        'page3 = widgets.Text()\n' +
        'multicontainer.children = [page1, page2, page3]\n' +
        'display(multicontainer)\n' +
        'multicontainer.selected_index = 0\n' +
        'print("Success")\n');
    this.execute_cell_then(multicontainer1_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create multicontainer cell executed with correct output. (1)');
    });

    // Wait for the widget to actually display.
    this.wait_for_element(multicontainer1_index, multicontainer1_query);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(multicontainer1_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(multicontainer1_index, multicontainer1_query),
            'Widget tab list exists.');

        // JQuery selector is 1 based
        this.click(multicontainer1_query + ' li:nth-child(2) a');
    });

    this.wait_for_idle();

    index = this.append_cell(
        'print(multicontainer.selected_index)\n' +
        'multicontainer.selected_index = 2'); // 0 based
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', // 0 based
            'selected_index property updated with tab change.');

        // JQuery selector is 1 based
        this.test.assert(!this.cell_element_function(multicontainer1_index, multicontainer1_query + ' li:nth-child(1)', 'hasClass', ['active']),
                "Tab 1 is not selected.");
        this.test.assert(!this.cell_element_function(multicontainer1_index, multicontainer1_query + ' li:nth-child(2)', 'hasClass', ['active']),
                "Tab 2 is not selected.");
        this.test.assert(this.cell_element_function(multicontainer1_index, multicontainer1_query + ' li:nth-child(3)', 'hasClass', ['active']),
                "Tab 3 is selected.");
    });

    index = this.append_cell('multicontainer.set_title(1, "hello")\nprint("Success")'); // 0 based
    this.execute_cell_then(index, function(index){
        this.test.assert(this.cell_element_function(multicontainer1_index, multicontainer1_query +
            ' li:nth-child(2) a', 'html') == 'hello',
            'Tab page title set (after display).');
    });

    // Test accordion view
    var multicontainer2_query = '.widget-area .widget-subarea .panel-group';
    var multicontainer2_index = this.append_cell(
        'multicontainer = widgets.Accordion()\n' +
        'page1 = widgets.Text()\n' +
        'page2 = widgets.Text()\n' +
        'page3 = widgets.Text()\n' +
        'multicontainer.children = [page1, page2, page3]\n' +
        'multicontainer.set_title(2, "good")\n' +
        'display(multicontainer)\n' +
        'multicontainer.selected_index = 0\n' +
        'print("Success")\n');
    this.execute_cell_then(multicontainer2_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create multicontainer cell executed with correct output. (2)');
    });

    // Wait for the widget to actually display.
    this.wait_for_element(multicontainer2_index, multicontainer2_query);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(multicontainer2_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(multicontainer2_index, multicontainer2_query),
            'Widget accordion exists.');

        this.test.assert(this.cell_element_exists(multicontainer2_index, multicontainer2_query + 
            ' .panel:nth-child(1) .panel-collapse'),
            'First accordion page exists.');

        // JQuery selector is 1 based
        this.test.assert(this.cell_element_function(multicontainer2_index, multicontainer2_query + 
            ' .panel.panel-default:nth-child(3) .panel-heading .accordion-toggle', 
            'html')=='good', 'Accordion page title set (before display).');

        // JQuery selector is 1 based
        this.click(multicontainer2_query + ' .panel:nth-child(2) .panel-heading .accordion-toggle');
    });

    this.wait_for_idle();

    index = this.append_cell('print(multicontainer.selected_index)'); // 0 based
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', // 0 based
            'selected_index property updated with tab change.');

        var is_collapsed = this.evaluate(function(s){
             return $(s + ' div.panel:nth-child(2) a').hasClass('collapsed'); // 1 based
        }, {s: multicontainer2_query});
        this.test.assertEquals(is_collapsed, false, 'Was tab actually opened?');
    });
});