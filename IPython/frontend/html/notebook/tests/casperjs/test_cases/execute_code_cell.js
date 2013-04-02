//
// Test code cell execution.
//
casper.openNewNotebook();

casper.then(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('a=10; print a');
        cell.execute();
    });
});

casper.wait(2000);

casper.then(function () {
    var result = this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        var output = cell.element.find('.output_area').find('pre').html();
        return output;
    })
    this.test.assertEquals(result, '10\n', 'stdout output matches')
});

casper.deleteCurrentNotebook();

casper.run(function() {
    this.test.done();
});
