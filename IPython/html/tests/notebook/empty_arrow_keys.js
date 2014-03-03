//
// Check for errors with up and down arrow presses in an empty notebook.
//
casper.notebook_test(function () {
    var result = this.evaluate(function() {
        var ncells = IPython.notebook.ncells();
        var i;
        
        // Delete all cells.
        for (i = 0; i < ncells; i++) {
            IPython.notebook.delete_cell();
        }
        
        // Simulate the "up arrow" and "down arrow" keys.
        //
        IPython.keyboard.trigger_keydown('up');
        IPython.keyboard.trigger_keydown('down');
        return true;
    });
    this.test.assertTrue(result, 'Up/down arrow okay in empty notebook.');
});
