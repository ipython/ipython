
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
    
    this.thenEvaluate(function() {
        IPython.notebook.default_cell_type = 'code';
    });
    
    this.then(function () {
        // Cell insertion
        this.select_cell(2);
        this.trigger_keydown('m'); // Make it markdown
        this.trigger_keydown('a'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'a; New cell 2 text is empty');
        this.test.assertEquals(this.get_cell(2).cell_type, 'code', 'a; inserts a code cell');
        this.validate_notebook_state('a', 'command', 2);
        this.trigger_keydown('b'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'b; Cell 2 text is still empty');
        this.test.assertEquals(this.get_cell_text(3), '', 'b; New cell 3 text is empty');
        this.test.assertEquals(this.get_cell(3).cell_type, 'code', 'b; inserts a code cell');
        this.validate_notebook_state('b', 'command', 3);
    });
    
    this.thenEvaluate(function() {
        IPython.notebook.class_config.set('default_cell_type', 'selected');
    });
    
    this.then(function () {
        this.select_cell(2);
        this.trigger_keydown('m'); // switch it to markdown for the next test
        this.test.assertEquals(this.get_cell(2).cell_type, 'markdown', 'test cell is markdown');
        this.trigger_keydown('a'); // new cell above
        this.test.assertEquals(this.get_cell(2).cell_type, 'markdown', 'a; inserts a markdown cell when markdown selected');
        this.trigger_keydown('b'); // new cell below
        this.test.assertEquals(this.get_cell(3).cell_type, 'markdown', 'b; inserts a markdown cell when markdown selected');
    });
    
    this.thenEvaluate(function() {
        IPython.notebook.class_config.set('default_cell_type', 'above');
    });
    
    this.then(function () {
        this.select_cell(2);
        this.trigger_keydown('y'); // switch it to code for the next test
        this.test.assertEquals(this.get_cell(2).cell_type, 'code', 'test cell is code');
        this.trigger_keydown('b'); // new cell below
        this.test.assertEquals(this.get_cell(3).cell_type, 'code', 'b; inserts a code cell below code cell');
        this.trigger_keydown('a'); // new cell above
        this.test.assertEquals(this.get_cell(3).cell_type, 'code', 'a; inserts a code cell above code cell');
    });
    
    this.thenEvaluate(function() {
        IPython.notebook.class_config.set('default_cell_type', 'below');
    });
    
    this.then(function () {
        this.select_cell(2);
        this.trigger_keydown('r'); // switch it to markdown for the next test
        this.test.assertEquals(this.get_cell(2).cell_type, 'raw', 'test cell is raw');
        this.trigger_keydown('a'); // new cell above
        this.test.assertEquals(this.get_cell(2).cell_type, 'raw', 'a; inserts a raw cell above raw cell');
        this.trigger_keydown('y'); // switch it to code for the next test
        this.trigger_keydown('b'); // new cell below
        this.test.assertEquals(this.get_cell(3).cell_type, 'raw', 'b; inserts a raw cell below raw cell');
    });
});
