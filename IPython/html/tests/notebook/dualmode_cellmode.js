// Test keyboard shortcuts that change the cell's mode.

// Test
casper.notebook_test(function () {
    this.then(function () {
        // Cell mode change
        this.select_cell(0);
        this.trigger_keydown('esc','r');
        this.test.assertEquals(this.get_cell(0).cell_type, 'raw', 'r; cell is raw');
        this.trigger_keydown('1');
        this.test.assertEquals(this.get_cell(0).cell_type, 'heading', '1; cell is heading');
        this.test.assertEquals(this.get_cell(0).level, 1, '1; cell is level 1 heading');
        this.trigger_keydown('2');
        this.test.assertEquals(this.get_cell(0).level, 2, '2; cell is level 2 heading');
        this.trigger_keydown('3');
        this.test.assertEquals(this.get_cell(0).level, 3, '3; cell is level 3 heading');
        this.trigger_keydown('4');
        this.test.assertEquals(this.get_cell(0).level, 4, '4; cell is level 4 heading');
        this.trigger_keydown('5');
        this.test.assertEquals(this.get_cell(0).level, 5, '5; cell is level 5 heading');
        this.trigger_keydown('6');
        this.test.assertEquals(this.get_cell(0).level, 6, '6; cell is level 6 heading');
        this.trigger_keydown('m');
        this.test.assertEquals(this.get_cell(0).cell_type, 'markdown', 'm; cell is markdown');
        this.trigger_keydown('y');
        this.test.assertEquals(this.get_cell(0).cell_type, 'code', 'y; cell is code');
    });
});