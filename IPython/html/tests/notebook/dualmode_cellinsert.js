
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
        // Cell insertion
        this.select_cell(2);
        this.trigger_keydown('a'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'a; New cell 2 text is empty');
        this.test.assertEquals(this.get_cell(2).cell_type, 'code', 'a; inserts a code cell when on code cell');
        this.validate_notebook_state('a', 'command', 2);
        this.trigger_keydown('b'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'b; Cell 2 text is still empty');
        this.test.assertEquals(this.get_cell_text(3), '', 'b; New cell 3 text is empty');
        this.test.assertEquals(this.get_cell(3).cell_type, 'code', 'b; inserts a code cell when on code cell');
        this.validate_notebook_state('b', 'command', 3);
    });
    this.then(function () {
        // Cell insertion
        this.select_cell(2);
        this.trigger_keydown('m'); // switch it to markdown for the next test
        this.trigger_keydown('a'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'a; New cell 2 text is empty');
        this.test.assertEquals(this.get_cell(2).cell_type, 'markdown', 'a; inserts a markdown cell when on markdown cell');
        this.validate_notebook_state('a', 'command', 2);
        this.trigger_keydown('b'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'b; Cell 2 text is still empty');
        this.test.assertEquals(this.get_cell(3).cell_type, 'markdown', 'b; inserts a markdown cell when on markdown cell');
        this.validate_notebook_state('b', 'command', 3);
    });
});
