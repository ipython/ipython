
       
// Test
casper.notebook_test(function () {
    var a = 'print("a")';
    var index = this.append_cell(a);
    this.execute_cell_then(index);

    var b = 'print("b")';
    index = this.append_cell(b);
    this.execute_cell_then(index);

    var c = 'print("c")';
    index = this.append_cell(c);
    this.execute_cell_then(index);

    this.then(function () {
         // Copy/paste/cut
        var num_cells = this.get_cells_length();
        this.test.assertEquals(this.get_cell_text(1), a, 'Verify that cell 1 is a');
        this.select_cell(1);
        this.trigger_keydown('x'); // Cut
        this.validate_notebook_state('x', 'command', 1);
        this.test.assertEquals(this.get_cells_length(), num_cells-1,  'Verify that a cell was removed.');
        this.test.assertEquals(this.get_cell_text(1), b, 'Verify that cell 2 is now where cell 1 was.');
        this.select_cell(2);
        this.trigger_keydown('v'); // Paste
        this.validate_notebook_state('v', 'command', 3); // Selection should move to pasted cell, below current cell.
        this.test.assertEquals(this.get_cell_text(3), a, 'Verify that cell 3 has the cut contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells,  'Verify a the cell was added.');
        this.trigger_keydown('v'); // Paste
        this.validate_notebook_state('v', 'command', 4); // Selection should move to pasted cell, below current cell.
        this.test.assertEquals(this.get_cell_text(4), a, 'Verify that cell 4 has the cut contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells+1,  'Verify a the cell was added.');
        this.select_cell(1);
        this.trigger_keydown('c'); // Copy
        this.validate_notebook_state('c', 'command', 1);
        this.test.assertEquals(this.get_cell_text(1), b, 'Verify that cell 1 is b');
        this.select_cell(2);
        this.trigger_keydown('c'); // Copy
        this.validate_notebook_state('c', 'command', 2);
        this.test.assertEquals(this.get_cell_text(2), c, 'Verify that cell 2 is c');
        this.select_cell(4);
        this.trigger_keydown('v'); // Paste
        this.validate_notebook_state('v', 'command', 5);
        this.test.assertEquals(this.get_cell_text(2), c, 'Verify that cell 2 still has the copied contents.');
        this.test.assertEquals(this.get_cell_text(5), c, 'Verify that cell 5 has the copied contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells+2,  'Verify a the cell was added.');
        this.select_cell(0);
        this.trigger_keydown('shift-v'); // Paste
        this.validate_notebook_state('shift-v', 'command', 0);
        this.test.assertEquals(this.get_cell_text(0), c, 'Verify that cell 0 has the copied contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells+3,  'Verify a the cell was added.');
    });
});