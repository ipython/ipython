// Test container class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var container_index = this.append_cell(
        'container = widgets.Box()\n' +
        'button = widgets.Button()\n'+
        'container.children = [button]\n'+
        'display(container)\n'+
        'container._dom_classes = ["my-test-class"]\n'+
        'print("Success")\n');
    this.execute_cell_then(container_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create container cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-box'),
            'Widget container exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .my-test-class'),
            '_dom_classes works.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .my-test-class button'),
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

    index = this.append_cell(
        'display(button)\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Display container child executed with correct output.');

        this.test.assert(! this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-box'),
            'Parent container not displayed.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea button'),
            'Child displayed.');
    });
});