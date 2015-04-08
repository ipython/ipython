// Test keyboard shortcuts that change the cell's mode.

// Test
casper.notebook_test(function () {
    this.then(function () {
        // Cell mode change
        var index = 0;
        this.select_cell(index);
        var a = 'hello\nmulti\nline';
        this.set_cell_text(index, a);
        this.trigger_keydown('esc','r');
        this.test.assertEquals(this.get_cell(index).cell_type, 'raw', 'r; cell is raw');
        this.trigger_keydown('1');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '1; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '# ' + a, '1; markdown heading');
        this.trigger_keydown('2');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '2; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '## ' + a, '2; markdown heading');
        this.trigger_keydown('3');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '3; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '### ' + a, '3; markdown heading');
        this.trigger_keydown('4');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '4; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '#### ' + a, '4; markdown heading');
        this.trigger_keydown('5');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '5; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '##### ' + a, '5; markdown heading');
        this.trigger_keydown('6');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '6; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '###### ' + a, '6; markdown heading');
        this.trigger_keydown('m');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', 'm; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '###### ' + a, 'm; still markdown heading');
        this.trigger_keydown('y');
        this.test.assertEquals(this.get_cell(index).cell_type, 'code', 'y; cell is code');
        this.test.assertEquals(this.get_cell_text(index), '###### ' + a, 'y; still has hashes');
        this.trigger_keydown('1');
        this.test.assertEquals(this.get_cell(index).cell_type, 'markdown', '1; cell is markdown');
        this.test.assertEquals(this.get_cell_text(index), '# ' + a, '1; markdown heading');
    });
});