// Test the notebook dual mode feature.

// Test
casper.notebook_test(function () {
    var index = this.append_cell('print("a")');
    this.execute_cell_then(index);
    index = this.append_cell('print("b")');
    this.execute_cell_then(index);
    index = this.append_cell('print("c")');
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

        // shift+enter tests.
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

        // ctrl+enter tests.
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

        // alt+enter tests.
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
        this.test.assertEquals(this.get_cells().length, 8, '*-enter commands added cells where needed.');
        this.select_cell(7);
        this.validate_state('click cell ' + 7 + ' and esc', 'command', 7);

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

        this.trigger_keydown('d', 'd');
        this.test.assertEquals(this.get_cells().length, 7, 'dd actually deletes a cell');
        this.validate_state('dd', 'command', 6);

        // Make sure that if the time between d presses is too long 
        this.trigger_keydown('d');
    });
    this.wait(1000);
    this.then(function () {
        this.trigger_keydown('d');

        this.test.assertEquals(this.get_cells().length, 7, "d, 1 second wait, d doesn't delete a cell");
        this.validate_state('d, 1 second wait, d', 'command', 6);
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
        this.validate_state('select 6', 'command', 5);
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
        var cells = this.get_cells();
        for (var i = 0; i < cells.length; i++) {
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

    this.get_cells = function() {
        return this.evaluate(function() {
            return IPython.notebook.get_cells();
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
        var cells = this.get_cells();
        for (var j = 0; j < cells.length; j++) {
            if (j === i) {
                if (this._has_cell_class(j, off_class) || !this._has_cell_class(j, on_class)) {
                    return false;
                }
            } else {
                if (!this._has_cell_class(j, off_class) || this._has_cell_class(j, on_class)) {
                    return false;
                }
            }
        }
        return true;
    };

    this._has_cell_class = function(index, classes) {
        return this.evaluate(function(i, c) {
            var cell = IPython.notebook.get_cell(i);
            if (cell) {
                return cell.element.hasClass(c);
            }
            return false;
        }, {i : index, c: classes});
    };
});
