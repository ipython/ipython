//
// Test that a Markdown cell is rendered to HTML.
//
casper.notebook_test(function () {
    // Test JavaScript models.
    var output = this.evaluate(function () {
        IPython.notebook.to_markdown();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('# Foo');
        cell.render();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<h1 id=\"foo\">Foo</h1>', 'Markdown JS API works.');
    
    // Test menubar entries.
    output = this.evaluate(function () {
        $('#to_code').mouseenter().click();
        $('#to_markdown').mouseenter().click();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('# Bar');
        $('#run_cell').mouseenter().click();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<h1 id=\"bar\">Bar</h1>', 'Markdown menubar items work.');
    
    // Test toolbar buttons.
    output = this.evaluate(function () {
        $('#cell_type').val('code').change();
        $('#cell_type').val('markdown').change();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('# Baz');
        $('#run_b').click();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<h1 id=\"baz\">Baz</h1>', 'Markdown toolbar items work.');
    
    // Test JavaScript models.
    var output = this.evaluate(function () {

        var cell = IPython.notebook.insert_cell_at_index('markdown', 0);
        cell.set_text('# Qux');
        cell.render();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<h1 id=\"qux\">Qux</h1>', 'Markdown JS API works.');
    
});
