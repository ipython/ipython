// Test container class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var container_index = this.append_cell(
        'container = widgets.ContainerWidget()\n' +
        'button = widgets.ButtonWidget()\n'+
        'container.children = [button]\n'+
        'display(container)\n'+
        'container.add_class("my-test-class")\n'+
        'print("Success")\n');
    this.execute_cell_then(container_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create container cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-container'),
            'Widget container exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .my-test-class'),
            'add_class works.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .my-test-class button'),
            'Container parent/child relationship works.');
    });

    index = this.append_cell(
        'container.set_css("float", "right")\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Set container class CSS cell executed with correct output.');
        
        this.test.assert(this.cell_element_function(container_index, 
            '.widget-area .widget-subarea .my-test-class', 'css', ['float'])=='right',
            'set_css works.');
    });

    index = this.append_cell(
        'container.remove_class("my-test-class")\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Remove container class cell executed with correct output.');

        this.test.assert(! this.cell_element_exists(container_index, 
            '.widget-area .widget-subarea .my-test-class'),
            'remove_class works.');
    });

    index = this.append_cell(
        'display(button)\n'+
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Display container child executed with correct output.');

        this.test.assert(! this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-container'),
            'Parent container not displayed.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea button'),
            'Child displayed.');
    });
});