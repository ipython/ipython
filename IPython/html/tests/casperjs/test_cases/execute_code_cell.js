//
// Test code cell execution.
//
casper.notebookTest(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('a=10; print a');
        cell.execute();
    });

    this.wait(2000);

    this.then(function () {
        var result = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var output = cell.element.find('.output_area').find('pre').html();
            return output;
        })
        this.test.assertEquals(result, '10\n', 'stdout output matches')
    });
});
