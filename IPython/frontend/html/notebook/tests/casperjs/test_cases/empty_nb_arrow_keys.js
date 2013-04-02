//
// Check for errors with up and down arrow presses in an empty notebook.
//
casper.openNewNotebook();

casper.then(function () {
    var result = this.evaluate(function() {
        var ncells = IPython.notebook.ncells(),
            i;
        
        // Delete all cells.
        for (i = 0; i < ncells; i++) {
            IPython.notebook.delete_cell();
        }
        
        // Simulate the "up arrow" and "down arrow" keys.
        var up_press = jQuery.Event("keydown", {which: 38});
        $(document).trigger(up_press);
        var down_press = jQuery.Event("keydown", {which: 40});
        $(document).trigger(down_press);
        return true;
    });
    casper.test.assertTrue(result, 'Trivial assertion to check for JS errors');
});

casper.deleteCurrentNotebook();

// Run the browser automation.
casper.run(function() {
    this.test.done();
});
