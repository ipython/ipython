
// Test
casper.notebook_test(function () {
    var that = this;
    var cell_is_deletable = function (index) {
        // Get the deletable status of a cell.
        return that.evaluate(function (index) {
            var cell = IPython.notebook.get_cell(index);
            return cell.is_deletable();
        }, index);
    };

    var a = 'print("a")';
    var index = this.append_cell(a);

    var b = 'print("b")';
    index = this.append_cell(b);

    var c = 'print("c")';
    index = this.append_cell(c);

    this.thenEvaluate(function() {
        IPython.notebook.get_cell(1).metadata.deletable = false;
        IPython.notebook.get_cell(2).metadata.deletable = 0; // deletable only when exactly false
        IPython.notebook.get_cell(3).metadata.deletable = true;
    });

    this.then(function () {
        // Check deletable status of the cells
        this.test.assert(cell_is_deletable(0), 'Cell 0 is deletable');
        this.test.assert(!cell_is_deletable(1), 'Cell 1 is not deletable');
        this.test.assert(cell_is_deletable(2), 'Cell 2 is deletable');
        this.test.assert(cell_is_deletable(3), 'Cell 3 is deletable');
    });

    // Try to delete cell 0 (should succeed)
    this.then(function () {
        this.select_cell(0);
        this.trigger_keydown('esc');
        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells_length(), 3, 'Delete cell 0: There are now 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Delete cell 0: Cell 1 is now cell 0');
        this.test.assertEquals(this.get_cell_text(1), b, 'Delete cell 0: Cell 2 is now cell 1');
        this.test.assertEquals(this.get_cell_text(2), c, 'Delete cell 0: Cell 3 is now cell 2');
        this.validate_notebook_state('dd', 'command', 0);
    });

    // Try to delete cell 0 (should fail)
    this.then(function () {
        this.select_cell(0);
        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells_length(), 3, 'Delete cell 0: There are still 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Delete cell 0: Cell 0 was not deleted');
        this.test.assertEquals(this.get_cell_text(1), b, 'Delete cell 0: Cell 1 was not affected');
        this.test.assertEquals(this.get_cell_text(2), c, 'Delete cell 0: Cell 2 was not affected');
        this.validate_notebook_state('dd', 'command', 0);
    });

    // Try to delete cell 1 (should succeed)
    this.then(function () {
        this.select_cell(1);
        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells_length(), 2, 'Delete cell 1: There are now 2 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Delete cell 1: Cell 0 was not affected');
        this.test.assertEquals(this.get_cell_text(1), c, 'Delete cell 1: Cell 1 was not affected');
        this.validate_notebook_state('dd', 'command', 1);
    });

    // Try to delete cell 1 (should succeed)
    this.then(function () {
        this.select_cell(1);
        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells_length(), 1, 'Delete cell 1: There is now 1 cell');
        this.test.assertEquals(this.get_cell_text(0), a, 'Delete cell 2: Cell 0 was not affected');
        this.validate_notebook_state('dd', 'command', 0);
    });

    // Change the deletable status of the last cells
    this.thenEvaluate(function() {
        IPython.notebook.get_cell(0).metadata.deletable = true;
    });

    this.then(function () {
        // Check deletable status of the cell
        this.test.assert(cell_is_deletable(0), 'Cell 0 is deletable');

        // Try to delete the last cell (should succeed)
        this.select_cell(0);
        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells_length(), 1, 'Delete last cell: There is still 1 cell');
        this.test.assertEquals(this.get_cell_text(0), "", 'Delete last cell: Cell 0 was deleted');
        this.validate_notebook_state('dd', 'command', 0);
    });

    // Make sure copied cells are deletable
    this.thenEvaluate(function() {
        IPython.notebook.get_cell(0).metadata.deletable = false;
    });
    this.then(function () {
        this.select_cell(0);
        this.trigger_keydown('c', 'v');
        this.test.assertEquals(this.get_cells_length(), 2, 'Copy cell: There are 2 cells');
        this.test.assert(!cell_is_deletable(0), 'Cell 0 is not deletable');
        this.test.assert(cell_is_deletable(1), 'Cell 1 is deletable');
        this.validate_notebook_state('cv', 'command', 1);
    });
});
