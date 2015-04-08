
// Test
casper.notebook_test(function () {
    var a = 'ab\ncd';
    var b = 'print("b")';
    var c = 'print("c")';

    var that = this;
    var cell_is_mergeable = function (index) {
        // Get the mergeable status of a cell.
        return that.evaluate(function (index) {
            var cell = IPython.notebook.get_cell(index);
            return cell.is_mergeable();
        }, index);
    };

    var cell_is_splittable = function (index) {
        // Get the splittable status of a cell.
        return that.evaluate(function (index) {
            var cell = IPython.notebook.get_cell(index);
            return cell.is_splittable();
        }, index);
    };

    var close_dialog = function () {
        this.evaluate(function(){
            $('div.modal-footer button.btn-default').click();
        }, {});
    };

    this.then(function () {
        // Split and merge cells
        this.select_cell(0);
        this.trigger_keydown('a', 'enter'); // Create cell above and enter edit mode.
        this.validate_notebook_state('a, enter', 'edit', 0);
        this.set_cell_text(0, 'abcd');
        this.set_cell_editor_cursor(0, 0, 2);
        this.test.assertEquals(this.get_cell_text(0), 'abcd', 'Verify that cell 0 has the new contents.');
        this.trigger_keydown('ctrl-shift-subtract'); // Split
        this.test.assertEquals(this.get_cell_text(0), 'ab', 'split; Verify that cell 0 has the first half.');
        this.test.assertEquals(this.get_cell_text(1), 'cd', 'split; Verify that cell 1 has the second half.');
        this.validate_notebook_state('split', 'edit', 1);
        this.select_cell(0); // Move up to cell 0
        this.trigger_keydown('shift-m'); // Merge
        this.validate_notebook_state('merge', 'command', 0);
        this.test.assertEquals(this.get_cell_text(0), a, 'merge; Verify that cell 0 has the merged contents.');
    });

    // add some more cells and test splitting/merging when a cell is not deletable
    this.then(function () {
        this.append_cell(b);
        this.append_cell(c);
    });

    this.thenEvaluate(function() {
        IPython.notebook.get_cell(1).metadata.deletable = false;
    });

    // Check that merge/split status are correct
    this.then(function () {
        this.test.assert(cell_is_splittable(0), 'Cell 0 is splittable');
        this.test.assert(cell_is_mergeable(0), 'Cell 0 is mergeable');
        this.test.assert(!cell_is_splittable(1), 'Cell 1 is not splittable');
        this.test.assert(!cell_is_mergeable(1), 'Cell 1 is not mergeable');
        this.test.assert(cell_is_splittable(2), 'Cell 2 is splittable');
        this.test.assert(cell_is_mergeable(2), 'Cell 2 is mergeable');
    });

    // Try to merge cell 0 below with cell 1
    this.then(function () {
        this.select_cell(0);
        this.trigger_keydown('esc');
        this.trigger_keydown('shift-m');
        this.test.assertEquals(this.get_cells_length(), 3, 'Merge cell 0 down: There are still 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Merge cell 0 down: Cell 0 is unchanged');
        this.test.assertEquals(this.get_cell_text(1), b, 'Merge cell 0 down: Cell 1 is unchanged');
        this.test.assertEquals(this.get_cell_text(2), c, 'Merge cell 0 down: Cell 2 is unchanged');
        this.validate_notebook_state('shift-m', 'command', 0);
    });

    // Try to merge cell 1 above with cell 0
    this.then(function () {
        this.select_cell(1);
    });
    this.thenEvaluate(function () {
        IPython.notebook.merge_cell_above();
    });
    this.then(function () {
        this.test.assertEquals(this.get_cells_length(), 3, 'Merge cell 1 up: There are still 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Merge cell 1 up: Cell 0 is unchanged');
        this.test.assertEquals(this.get_cell_text(1), b, 'Merge cell 1 up: Cell 1 is unchanged');
        this.test.assertEquals(this.get_cell_text(2), c, 'Merge cell 1 up: Cell 2 is unchanged');
        this.validate_notebook_state('merge up', 'command', 1);
    });

    // Try to split cell 1
    this.then(function () {
        this.select_cell(1);
        this.trigger_keydown('enter');
        this.set_cell_editor_cursor(1, 0, 2);
        this.trigger_keydown('ctrl-shift-subtract'); // Split
        this.test.assertEquals(this.get_cells_length(), 3, 'Split cell 1: There are still 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Split cell 1: Cell 0 is unchanged');
        this.test.assertEquals(this.get_cell_text(1), b, 'Split cell 1: Cell 1 is unchanged');
        this.test.assertEquals(this.get_cell_text(2), c, 'Split cell 1: Cell 2 is unchanged');
        this.validate_notebook_state('ctrl-shift-subtract', 'edit', 1); 
    });

    // Try to merge cell 1 down
    this.then(function () {
        this.select_cell(1);
        this.trigger_keydown('esc');
        this.trigger_keydown('shift-m');
        this.test.assertEquals(this.get_cells_length(), 3, 'Merge cell 1 down: There are still 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Merge cell 1 down: Cell 0 is unchanged');
        this.test.assertEquals(this.get_cell_text(1), b, 'Merge cell 1 down: Cell 1 is unchanged');
        this.test.assertEquals(this.get_cell_text(2), c, 'Merge cell 1 down: Cell 2 is unchanged');
        this.validate_notebook_state('shift-m', 'command', 1);
    });

    // Try to merge cell 2 above with cell 1
    this.then(function () {
        this.select_cell(2);
    });
    this.thenEvaluate(function () {
        IPython.notebook.merge_cell_above();
    });
    this.then(function () {
        this.test.assertEquals(this.get_cells_length(), 3, 'Merge cell 2 up: There are still 3 cells');
        this.test.assertEquals(this.get_cell_text(0), a, 'Merge cell 2 up: Cell 0 is unchanged');
        this.test.assertEquals(this.get_cell_text(1), b, 'Merge cell 2 up: Cell 1 is unchanged');
        this.test.assertEquals(this.get_cell_text(2), c, 'Merge cell 2 up: Cell 2 is unchanged');
        this.validate_notebook_state('merge up', 'command', 2);
    });
});
