
// Test
casper.notebook_test(function () {
    var a = 'print("a")';
    var index = this.append_cell(a);
    this.execute_cell_then(index);

    var b = 'print("b")';
    index = this.append_cell(b);
    this.execute_cell_then(index);

    this.then(function () {
        // Cell movement ( ctrl-(k or j) )
        this.select_cell(2);
        this.test.assertEquals(this.get_cell_text(2), b, 'select 2; Cell 2 text is correct');
        this.trigger_keydown('ctrl-k'); // Move cell 2 up one
        this.test.assertEquals(this.get_cell_text(1), b, 'ctrl-k; Cell 1 text is correct');
        this.test.assertEquals(this.get_cell_text(2), a, 'ctrl-k; Cell 2 text is correct');
        this.validate_notebook_state('ctrl-k', 'command', 1);
        this.trigger_keydown('ctrl-j'); // Move cell 1 down one
        this.test.assertEquals(this.get_cell_text(1), a, 'ctrl-j; Cell 1 text is correct');
        this.test.assertEquals(this.get_cell_text(2), b, 'ctrl-j; Cell 2 text is correct');
        this.validate_notebook_state('ctrl-j', 'command', 2);
    });
});