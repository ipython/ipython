//
// Test that a Markdown cell is rendered to HTML.
//
casper.openNewNotebook();

casper.then(function () {
    var output = this.evaluate(function() {
        // Does it make more sense to test the UI or the JS API here?
        //
        // $('#cell_type').val('markdown');
        // $('#cell_type').change();
        // $('#run_b').click();
        //
        // $('#to_markdown').click(); // fails via jQuery UI menubar
        // $('#run_cell').click(); // fails via jQuery UI menubar
        IPython.notebook.to_markdown();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('# Foo');
        cell.render();
        return cell.get_rendered();
    });
    casper.test.assertEquals(output, '<h1>Foo</h1>', 'Markdown converted to HTML.');
});

casper.deleteCurrentNotebook();

// Run the browser automation.
casper.run(function() {
    this.test.done();
});
