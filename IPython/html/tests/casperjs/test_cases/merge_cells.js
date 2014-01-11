//
// Test merging two notebook cells.
//
casper.notebook_test(function() {
    var output = this.evaluate(function () {
        // Fill in test data.
        IPython.notebook.command_mode();
        var set_cell_text = function () {
            var cell_one = IPython.notebook.get_selected_cell();
            cell_one.set_text('a = 5');
            
            IPython.utils.press(IPython.keycodes.b)
            var cell_two = IPython.notebook.get_selected_cell();
            cell_two.set_text('print(a)');
        };
        
        // merge_cell_above()
        set_cell_text();
        IPython.notebook.merge_cell_above();
        var merged_above = IPython.notebook.get_selected_cell();
        
        // merge_cell_below()
        set_cell_text();
        IPython.notebook.select(0);
        IPython.notebook.merge_cell_below();
        var merged_below = IPython.notebook.get_selected_cell();
        
        return {
            above: merged_above.get_text(),
            below: merged_below.get_text()
        };
    });
    
    this.test.assertEquals(output.above, 'a = 5\nprint(a)',
                           'Successful merge_cell_above().');
    this.test.assertEquals(output.below, 'a = 5\nprint(a)',
                           'Successful merge_cell_below().');
});
