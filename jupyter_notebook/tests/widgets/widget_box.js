// Test container class
casper.notebook_test(function () {

    // Create a box widget.
    var container_index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'container = widgets.Box()\n' +
        'button = widgets.Button()\n'+
        'container.children = [button]\n'+
        'display(container)\n'+
        'container._dom_classes = ["my-test-class"]\n'+
        'print("Success")\n');
    this.execute_cell_then(container_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create container cell executed with correct output.');
    });

    // Wait for the widgets to actually display.
    var widget_box_selector = '.widget-area .widget-subarea .widget-box';
    var widget_box_button_selector = '.widget-area .widget-subarea .widget-box button';
    this.wait_for_element(container_index, widget_box_selector);
    this.wait_for_element(container_index, widget_box_button_selector);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(container_index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(container_index, 
            widget_box_selector),
            'Widget container exists.');

        this.test.assert(this.cell_element_exists(container_index, 
            '.widget-area .widget-subarea .my-test-class'),
            '_dom_classes works.');

        this.test.assert(this.cell_element_exists(container_index, 
            widget_box_button_selector),
            'Container parent/child relationship works.');
    });

    index = this.append_cell(
        'container.box_style = "success"\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Set box_style cell executed with correct output.');

        this.test.assert(this.cell_element_exists(container_index, 
            '.widget-box.alert-success'),
            'Set box_style works.');
    });

    index = this.append_cell(
        'container._dom_classes = []\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Remove container class cell executed with correct output.');

        this.test.assert(! this.cell_element_exists(container_index, 
            '.widget-area .widget-subarea .my-test-class'),
            '_dom_classes can be used to remove a class.');
    });

    var boxalone_index = this.append_cell(
        'display(button)\n'+
        'print("Success")\n');
    this.execute_cell_then(boxalone_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Display container child executed with correct output.');
    });

    // Wait for the widget to actually display.
    var widget_button_selector = '.widget-area .widget-subarea button';
    this.wait_for_element(boxalone_index, widget_button_selector);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(! this.cell_element_exists(boxalone_index, 
            widget_box_selector),
            'Parent container not displayed.');

        this.test.assert(this.cell_element_exists(boxalone_index, 
            widget_button_selector),
            'Child displayed.');
    });
});