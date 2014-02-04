// Test widget string class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var string_index = this.append_cell(
        'string_widget = [widgets.TextWidget(value = "xyz"),\n' +
        '    widgets.TextareaWidget(value = "xyz"),\n' +
        '    widgets.HTMLWidget(value = "xyz"),\n' +
        '    widgets.LatexWidget(value = "$\\\\LaTeX{}$")]\n' +
        '[display(widget) for widget in string_widget]\n'+
        'print("Success")');
    this.execute_cell_then(string_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
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

        this.test.assert(this.cell_element_exists(string_index, 
            '.widget-area .widget-subarea div span.MathJax_Preview'),
            'MathJax parsed the LaTeX successfully.');
    });
});