// Test widget string class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var string_index = this.append_cell(
        'string_widget = widgets.StringWidget()\n' +
        'display(string_widget)\n'+
        'display(string_widget, view_name="TextAreaView")\n' +
        'display(string_widget, view_name="HTMLView")\n' +
        'display(string_widget, view_name="LatexView")\n' +
        'string_widget.value = "xyz"\n' +
        'print("Success")');
    this.execute_cell_then(string_index, function(index){

        this.test.assert(this.get_output_cell(index).text == 'Success\n', 
            'Create string widget cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-hbox-single input[type=text]'),
            'Textbox exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-hbox textarea'),
            'Textarea exists.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox textarea', 'val')=='xyz',
            'Python set textarea value.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox-single input[type=text]', 'val')=='xyz',
            'Python set textbox value.');

        this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox-single input[type=text]', 'val', [''])
        this.sendKeys('.widget-area .widget-subarea .widget-hbox-single input[type=text]', 'abc');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox textarea', 'val')=='abc',
            'Textarea updated to textbox contents.');

        this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox textarea', 'val', ['']);
        this.sendKeys('.widget-area .widget-subarea .widget-hbox textarea', '$\\LaTeX{}$');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox-single input[type=text]', 'val')=='$\\LaTeX{}$',
            'Textbox updated to textarea contents.');
    });

    this.wait(500); // Wait for change to execute in kernel

    index = this.append_cell('print(string_widget.value)');
    this.execute_cell_then(index, function(index){
        this.test.assert(this.get_output_cell(index).text == '$\\LaTeX{}$\n', 
            'Python updated with correct string widget value.');

        this.test.assert(this.cell_element_exists(string_index, 
            '.widget-area .widget-subarea div span.MathJax_Preview'),
            'MathJax parsed the LaTeX successfully.');
    });
});