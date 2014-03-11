// Test the notebook dual mode feature.

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
        this.validate_state('initial state', 'edit', 0);
        this.trigger_keydown('esc');
        this.validate_state('esc', 'command', 0);
        this.trigger_keydown('down');
        this.validate_state('down', 'command', 1);
        this.trigger_keydown('enter');
        this.validate_state('enter', 'edit', 1);
        this.trigger_keydown('j');
        this.validate_state('j in edit mode', 'edit', 1);
        this.trigger_keydown('esc');
        this.validate_state('esc', 'command', 1);
        this.trigger_keydown('j');
        this.validate_state('j in command mode', 'command', 2);
        this.click_cell_editor(0);
        this.validate_state('click cell 0', 'edit', 0);
        this.click_cell_editor(3);
        this.validate_state('click cell 3', 'edit', 3);
        this.trigger_keydown('esc');
        this.validate_state('esc', 'command', 3);

        // Open keyboard help
        this.evaluate(function(){
            $('#keyboard_shortcuts a').click();
        }, {});

        this.trigger_keydown('k');
        this.validate_state('k in command mode while keyboard help is up', 'command', 3);

        // Close keyboard help
        this.evaluate(function(){
            $('div.modal button.close').click();
        }, {});

        this.trigger_keydown('k');
        this.validate_state('k in command mode', 'command', 2);
        this.click_cell_editor(0);
        this.validate_state('click cell 0', 'edit', 0);
        this.focus_notebook();
        this.validate_state('focus #notebook', 'command', 0);
        this.click_cell_editor(0);
        this.validate_state('click cell 0', 'edit', 0);
        this.focus_notebook();
        this.validate_state('focus #notebook', 'command', 0);
        this.click_cell_editor(3);
        this.validate_state('click cell 3', 'edit', 3);

        // shift+enter
        // last cell in notebook
        var base_index = 3;
        this.trigger_keydown('shift+enter'); // Creates one cell
        this.validate_state('shift+enter (no cell below)', 'edit', base_index + 1);
        // not last cell in notebook & starts in edit mode
        this.click_cell_editor(base_index);
        this.validate_state('click cell ' + base_index, 'edit', base_index);
        this.trigger_keydown('shift+enter');
        this.validate_state('shift+enter (cell exists below)', 'command', base_index + 1);
        // starts in command mode
        this.trigger_keydown('k');
        this.validate_state('k in comand mode', 'command', base_index);
        this.trigger_keydown('shift+enter');
        this.validate_state('shift+enter (start in command mode)', 'command', base_index + 1);

        // ctrl+enter
        // last cell in notebook
        base_index++;
        this.trigger_keydown('ctrl+enter');
        this.validate_state('ctrl+enter (no cell below)', 'command', base_index);
        // not last cell in notebook & starts in edit mode
        this.click_cell_editor(base_index-1);
        this.validate_state('click cell ' + (base_index-1), 'edit', base_index-1);
        this.trigger_keydown('ctrl+enter');
        this.validate_state('ctrl+enter (cell exists below)', 'command', base_index-1);
        // starts in command mode
        this.trigger_keydown('j');
        this.validate_state('j in comand mode', 'command', base_index);
        this.trigger_keydown('ctrl+enter');
        this.validate_state('ctrl+enter (start in command mode)', 'command', base_index);

        // alt+enter
        // last cell in notebook
        this.trigger_keydown('alt+enter'); // Creates one cell
        this.validate_state('alt+enter (no cell below)', 'edit', base_index + 1);
        // not last cell in notebook & starts in edit mode
        this.click_cell_editor(base_index);
        this.validate_state('click cell ' + base_index, 'edit', base_index);
        this.trigger_keydown('alt+enter'); // Creates one cell
        this.validate_state('alt+enter (cell exists below)', 'edit', base_index + 1);
        // starts in command mode
        this.trigger_keydown('esc', 'k');
        this.validate_state('k in comand mode', 'command', base_index);
        this.trigger_keydown('alt+enter'); // Creates one cell
        this.validate_state('alt+enter (start in command mode)', 'edit', base_index + 1);

        // Notebook will now have 8 cells, the index of the last cell will be 7.
        this.test.assertEquals(this.get_cells_length(), 8, '*-enter commands added cells where needed.');
        this.select_cell(7);
        this.validate_state('click cell ' + 7 + ' and esc', 'command', 7);

        // Cell mode change
        this.trigger_keydown('r');
        this.test.assertEquals(this.get_cell(7).cell_type, 'raw', 'r; cell is raw');
        this.trigger_keydown('1');
        this.test.assertEquals(this.get_cell(7).cell_type, 'heading', '1; cell is heading');
        this.test.assertEquals(this.get_cell(7).level, 1, '1; cell is level 1 heading');
        this.trigger_keydown('2');
        this.test.assertEquals(this.get_cell(7).level, 2, '2; cell is level 2 heading');
        this.trigger_keydown('3');
        this.test.assertEquals(this.get_cell(7).level, 3, '3; cell is level 3 heading');
        this.trigger_keydown('4');
        this.test.assertEquals(this.get_cell(7).level, 4, '4; cell is level 4 heading');
        this.trigger_keydown('5');
        this.test.assertEquals(this.get_cell(7).level, 5, '5; cell is level 5 heading');
        this.trigger_keydown('6');
        this.test.assertEquals(this.get_cell(7).level, 6, '6; cell is level 6 heading');
        this.trigger_keydown('m');
        this.test.assertEquals(this.get_cell(7).cell_type, 'markdown', 'm; cell is markdown');
        this.trigger_keydown('y');
        this.test.assertEquals(this.get_cell(7).cell_type, 'code', 'y; cell is code');

        // Cell deletion
        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells_length(), 7, 'dd actually deletes a cell');
        this.validate_state('dd', 'command', 6);

        // Make sure that if the time between d presses is too long, nothing gets removed.
        this.trigger_keydown('d');
    });
    this.wait(1000);
    this.then(function () {
        this.trigger_keydown('d');
        this.test.assertEquals(this.get_cells_length(), 7, "d, 1 second wait, d doesn't delete a cell");
        this.validate_state('d, 1 second wait, d', 'command', 6);

        // Up and down in command mode
        this.trigger_keydown('j');
        this.validate_state('j at end of notebook', 'command', 6);
        this.trigger_keydown('down');
        this.validate_state('down at end of notebook', 'command', 6);
        this.trigger_keydown('up');
        this.validate_state('up', 'command', 5);
        this.select_cell(0);
        this.validate_state('select 0', 'command', 0);
        this.trigger_keydown('k');
        this.validate_state('k at top of notebook', 'command', 0);
        this.trigger_keydown('up');
        this.validate_state('up at top of notebook', 'command', 0);
        this.trigger_keydown('down');
        this.validate_state('down', 'command', 1);

        // Up and down in edit mode
        this.click_cell_editor(6);
        this.validate_state('click cell 6', 'edit', 6);
        this.trigger_keydown('down');
        this.validate_state('down at end of notebook', 'edit', 6);
        this.trigger_keydown('up');
        this.validate_state('up', 'edit', 5);
        this.click_cell_editor(0);
        this.validate_state('click 0', 'edit', 0);
        this.trigger_keydown('up');
        this.validate_state('up at top of notebook', 'edit', 0);
        this.trigger_keydown('down');
        this.validate_state('down', 'edit', 1);

        // Markdown rendering / unredering
        this.select_cell(6);
        this.validate_state('select 6', 'command', 6);
        this.trigger_keydown('m');
        this.test.assertEquals(this.get_cell(6).cell_type, 'markdown', 'm; cell is markdown');
        this.test.assertEquals(this.get_cell(6).rendered, false, 'm; cell is rendered');
        this.trigger_keydown('enter');
        this.test.assertEquals(this.get_cell(6).rendered, false, 'enter; cell is unrendered');
        this.validate_state('enter', 'edit', 6);
        this.trigger_keydown('ctrl+enter');
        this.test.assertEquals(this.get_cell(6).rendered, true, 'ctrl+enter; cell is rendered');
        this.validate_state('enter', 'command', 6);
        this.trigger_keydown('enter');
        this.test.assertEquals(this.get_cell(6).rendered, false, 'enter; cell is unrendered');
        this.select_cell(5);
        this.test.assertEquals(this.get_cell(6).rendered, false, 'select 5; cell 6 is still unrendered');
        this.validate_state('select 5', 'command', 5);
        this.select_cell(6);
        this.validate_state('select 6', 'command', 6);
        this.trigger_keydown('ctrl+enter');
        this.test.assertEquals(this.get_cell(6).rendered, true, 'ctrl+enter; cell is rendered');
        this.select_cell(5);
        this.validate_state('select 5', 'command', 5);
        this.trigger_keydown('shift+enter');
        this.validate_state('shift+enter', 'command', 6);
        this.test.assertEquals(this.get_cell(6).rendered, true, 'shift+enter; cell is rendered');
        this.trigger_keydown('shift+enter'); // Creates one cell
        this.validate_state('shift+enter', 'edit', 7);
        this.test.assertEquals(this.get_cell(6).rendered, true, 'shift+enter; cell is rendered');

        // Cell movement ( ctrl+(k or j) )
        this.select_cell(2);
        this.test.assertEquals(this.get_cell_text(2), b, 'select 2; Cell 2 text is correct');
        this.trigger_keydown('ctrl+k'); // Move cell 2 up one
        this.test.assertEquals(this.get_cell_text(1), b, 'ctrl+k; Cell 1 text is correct');
        this.test.assertEquals(this.get_cell_text(2), a, 'ctrl+k; Cell 2 text is correct');
        this.validate_state('ctrl+k', 'command', 1);
        this.trigger_keydown('ctrl+j'); // Move cell 1 down one
        this.test.assertEquals(this.get_cell_text(1), a, 'ctrl+j; Cell 1 text is correct');
        this.test.assertEquals(this.get_cell_text(2), b, 'ctrl+j; Cell 2 text is correct');
        this.validate_state('ctrl+j', 'command', 2);

        // Cell insertion
        this.trigger_keydown('a'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'a; New cell 2 text is empty');
        this.validate_state('a', 'command', 2);
        this.trigger_keydown('b'); // Creates one cell
        this.test.assertEquals(this.get_cell_text(2), '', 'b; Cell 2 text is still empty');
        this.test.assertEquals(this.get_cell_text(3), '', 'b; New cell 3 text is empty');
        this.validate_state('b', 'command', 3);

        // Copy/paste/cut
        var num_cells = this.get_cells_length();
        this.test.assertEquals(this.get_cell_text(1), a, 'Verify that cell 1 is a');
        this.select_cell(1);
        this.trigger_keydown('x'); // Cut
        this.validate_state('x', 'command', 1);
        this.test.assertEquals(this.get_cells_length(), num_cells-1,  'Verify that a cell was removed.');
        this.test.assertEquals(this.get_cell_text(1), '', 'Verify that cell 2 is now where cell 1 was.');
        this.select_cell(2);
        this.trigger_keydown('v'); // Paste
        this.validate_state('v', 'command', 3); // Selection should move to pasted cell, below current cell.
        this.test.assertEquals(this.get_cell_text(3), a, 'Verify that cell 3 has the cut contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells,  'Verify a the cell was added.');
        this.trigger_keydown('v'); // Paste
        this.validate_state('v', 'command', 4); // Selection should move to pasted cell, below current cell.
        this.test.assertEquals(this.get_cell_text(4), a, 'Verify that cell 4 has the cut contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells+1,  'Verify a the cell was added.');
        this.select_cell(5);
        this.trigger_keydown('c'); // Copy
        this.validate_state('c', 'command', 5);
        this.test.assertEquals(this.get_cell_text(5), b, 'Verify that cell 5 is b');
        this.select_cell(6);
        this.trigger_keydown('c'); // Copy
        this.validate_state('c', 'command', 6);
        this.test.assertEquals(this.get_cell_text(6), c, 'Verify that cell 6 is c');
        this.trigger_keydown('v'); // Paste
        this.validate_state('v', 'command', 7);
        this.test.assertEquals(this.get_cell_text(6), c, 'Verify that cell 6 still has the copied contents.');
        this.test.assertEquals(this.get_cell_text(7), c, 'Verify that cell 7 has the copied contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells+2,  'Verify a the cell was added.');
        this.select_cell(0);
        this.trigger_keydown('shift+v'); // Paste
        this.validate_state('shift+v', 'command', 0);
        this.test.assertEquals(this.get_cell_text(0), c, 'Verify that cell 0 has the copied contents.');
        this.test.assertEquals(this.get_cells_length(), num_cells+3,  'Verify a the cell was added.');
        

    });

    // Utility functions.
    this.validate_state = function(message, mode, cell_index) {
        // General tests.
        this.test.assertEquals(this.get_keyboard_mode(), this.get_notebook_mode(),
            message + '; keyboard and notebook modes match');
        // Is codemirror focused appropriately?
        this.test.assert(this.is_editor_focus_valid(), message + '; cell editor focused appropriately');
        // Is the selected cell the only cell that is selected?
        if (cell_index!==undefined) {
            this.test.assert(this.is_only_cell_selected(cell_index),
                message + '; cell ' + cell_index + ' is the only cell selected');
        }

        // Mode specific tests.
        if (mode==='command') {
            // Are the notebook and keyboard manager in command mode?
            this.test.assertEquals(this.get_keyboard_mode(), 'command',
                message + '; in command mode');
            // Make sure there isn't a single cell in edit mode.
            this.test.assert(this.is_only_cell_edit(null),
                message + '; all cells in command mode');

        } else if (mode==='edit') {
            // Are the notebook and keyboard manager in edit mode?
            this.test.assertEquals(this.get_keyboard_mode(), 'edit',
                message + '; in edit mode');
            // Is the specified cell the only cell in edit mode?
            if (cell_index!==undefined) {
                this.test.assert(this.is_only_cell_edit(cell_index),
                    message + '; cell ' + cell_index + ' is the only cell in edit mode');
            }

        } else {
            this.test.assert(false, message + '; ' + mode + ' is an unknown mode');
        }
    };

    this.is_editor_focus_valid = function() {
        var cells_length = this.get_cells_length();
        for (var i = 0; i < cells_length; i++) {
            if (!this.is_cell_editor_focus_valid(i)) {
                return false;
            }
        }
        return true;
    };

    this.is_cell_editor_focus_valid = function(index) {
        var cell = this.get_cell(index);
        if (cell) {
            if (cell.mode == 'edit') {
                return this.is_cell_editor_focused(index);
            } else {
                return !this.is_cell_editor_focused(index);
            }
        }
        return true;
    };


    /* TODO: MOVE EVERYTHING BELOW THIS LINE INTO THE BASE (utils.js) */


    this.select_cell = function (index) {
        this.evaluate(function (i) {
            IPython.notebook.select(i);
        }, {i: index});
    };

    this.click_cell_editor = function(index) {
        // Code Mirror does not play nicely with emulated brower events.  
        // Instead of trying to emulate a click, here we run code similar to
        // the code used in Code Mirror that handles the mousedown event on a
        // region of codemirror that the user can focus.
        this.evaluate(function (i) {
            cm = IPython.notebook.get_cell(i).code_mirror;
            if (cm.options.readOnly != "nocursor" && (document.activeElement != cm.display.input))
                cm.display.input.focus();
        }, {i: index});
    };

    this.focus_notebook = function() {
        this.evaluate(function (){
            $('#notebook').focus();
        }, {});
    };

    this.trigger_keydown = function() {
        for (var i = 0; i < arguments.length; i++) {
            this.evaluate(function (k) {
                IPython.keyboard.trigger_keydown(k);
            }, {k: arguments[i]});    
        }
    };

    this.get_keyboard_mode = function() {
        return this.evaluate(function() {
            return IPython.keyboard_manager.mode;
        }, {});
    };

    this.get_notebook_mode = function() {
        return this.evaluate(function() {
            return IPython.notebook.mode;
        }, {});
    };

    this.get_cell = function(index) {
        return this.evaluate(function(i) {
            var cell = IPython.notebook.get_cell(i);
            if (cell) {
                return cell;
            }
            return null;
        }, {i : index});
    };

    this.is_cell_editor_focused = function(index) {
        return this.evaluate(function(i) {
            var cell = IPython.notebook.get_cell(i);
            if (cell) {
                return $(cell.code_mirror.getInputField()).is('.CodeMirror-focused *');
            }
            return false;
        }, {i : index});
    };

    this.is_only_cell_selected = function(index) {
        return this.is_only_cell_on(index, 'selected', 'unselected');
    };

    this.is_only_cell_edit = function(index) {
        return this.is_only_cell_on(index, 'edit_mode', 'command_mode');
    };

    this.is_only_cell_on = function(i, on_class, off_class) {
        var cells_length = this.get_cells_length();
        for (var j = 0; j < cells_length; j++) {
            if (j === i) {
                if (this.cell_has_class(j, off_class) || !this.cell_has_class(j, on_class)) {
                    return false;
                }
            } else {
                if (!this.cell_has_class(j, off_class) || this.cell_has_class(j, on_class)) {
                    return false;
                }
            }
        }
        return true;
    };

    this.cell_has_class = function(index, classes) {
        return this.evaluate(function(i, c) {
            var cell = IPython.notebook.get_cell(i);
            if (cell) {
                return cell.element.hasClass(c);
            }
            return false;
        }, {i : index, c: classes});
    };
});
