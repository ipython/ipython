// Test widget string class
casper.notebook_test(function () {
    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    var string_index = this.append_cell(
        'string_widget = [widgets.Text(value = "xyz", placeholder = "abc"),\n' +
        '    widgets.Textarea(value = "xyz", placeholder = "def"),\n' +
        '    widgets.HTML(value = "xyz"),\n' +
        '    widgets.Latex(value = "$\\\\LaTeX{}$")]\n' +
        '[display(widget) for widget in string_widget]\n'+
        'print("Success")');
    this.execute_cell_then(string_index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Create string widget cell executed with correct output.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-hbox input[type=text]'),
            'Textbox exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea .widget-hbox textarea'),
            'Textarea exists.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox textarea', 'val')=='xyz',
            'Python set textarea value.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox input[type=text]', 'val')=='xyz',
            'Python set textbox value.');

        this.test.assert(this.cell_element_exists(string_index, 
            '.widget-area .widget-subarea div span.MathJax_Preview'),
            'MathJax parsed the LaTeX successfully.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox textarea', 'attr', ['placeholder'])=='def',
            'Python set textarea placeholder.');

        this.test.assert(this.cell_element_function(index, 
            '.widget-area .widget-subarea .widget-hbox input[type=text]', 'attr', ['placeholder'])=='abc',
            'Python set textbox placehoder.');
    });
});
