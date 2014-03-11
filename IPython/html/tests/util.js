//
// Utility functions for the HTML notebook's CasperJS tests.
//

// Get the URL of a notebook server on which to run tests.
casper.get_notebook_server = function () {
    port = casper.cli.get("port")
    port = (typeof port === 'undefined') ? '8888' : port;
    return 'http://127.0.0.1:' + port
};

// Create and open a new notebook.
casper.open_new_notebook = function () {
    var baseUrl = this.get_notebook_server();
    this.start(baseUrl);
    this.thenClick('button#new_notebook');
    this.waitForPopup('');

    this.withPopup('', function () {this.waitForSelector('.CodeMirror-code');});
    this.then(function () {
        this.open(this.popups[0].url);
    });

    // Make sure the kernel has started
    this.waitFor( this.kernel_running  );
    // track the IPython busy/idle state
    this.thenEvaluate(function () {
        $([IPython.events]).on('status_idle.Kernel',function () {
            IPython._status = 'idle';
        });
        $([IPython.events]).on('status_busy.Kernel',function () {
            IPython._status = 'busy';
        });
    });
};

// Return whether or not the kernel is running.
casper.kernel_running = function kernel_running() {
    return this.evaluate(function kernel_running() {
        return IPython.notebook.kernel.running;
    });
};

// Shut down the current notebook's kernel.
casper.shutdown_current_kernel = function () {
    this.thenEvaluate(function() {
        IPython.notebook.kernel.kill();
    });
    // We close the page right after this so we need to give it time to complete.
    this.wait(1000);
};

// Delete created notebook.
casper.delete_current_notebook = function () {
    // For some unknown reason, this doesn't work?!?
    this.thenEvaluate(function() {
        IPython.notebook.delete();
    });
};

casper.wait_for_busy = function () {
    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython._status == 'busy';
        });
    });
};

casper.wait_for_idle = function () {
    this.waitFor(function () {
        return this.evaluate(function () {
            return IPython._status == 'idle';
        });
    });
};

// wait for the nth output in a given cell
casper.wait_for_output = function (cell_num, out_num) {
    this.wait_for_idle();
    out_num = out_num || 0;
    this.then(function() {
        this.waitFor(function (c, o) {
            return this.evaluate(function get_output(c, o) {
                var cell = IPython.notebook.get_cell(c);
                return cell.output_area.outputs.length > o;
            },
            // pass parameter from the test suite js to the browser code js
            {c : cell_num, o : out_num});
        });
    },
    function then() { },
    function timeout() {
        this.echo("wait_for_output timed out!");
    });
};

// wait for a widget msg que to reach 0
//
// Parameters
// ----------
// widget_info : object
//      Object which contains info related to the widget.  The model_id property
//      is used to identify the widget.
casper.wait_for_widget = function (widget_info) {
    this.waitFor(function () {
        var pending = this.evaluate(function (m) {
            return IPython.notebook.kernel.widget_manager.get_model(m).pending_msgs;
        }, {m: widget_info.model_id});

        if (pending == 0) {
            return true;
        } else {
            return false;
        }
    });
}

// return an output of a given cell
casper.get_output_cell = function (cell_num, out_num) {
    out_num = out_num || 0;
    var result = casper.evaluate(function (c, o) {
        var cell = IPython.notebook.get_cell(c);
        return cell.output_area.outputs[o];
    },
    {c : cell_num, o : out_num});
    if (!result) {
        var num_outputs = casper.evaluate(function (c) {
            var cell = IPython.notebook.get_cell(c);
            return cell.output_area.outputs.length;
        },
        {c : cell_num});
        this.test.assertTrue(false,
            "Cell " + cell_num + " has no output #" + out_num + " (" + num_outputs + " total)"
        );
    } else {
        return result;
    }
};

// return the number of cells in the notebook
casper.get_cells_length = function () {
    var result = casper.evaluate(function () {
        return IPython.notebook.get_cells().length;
    })
    return result;
};

// Set the text content of a cell.
casper.set_cell_text = function(index, text){
    this.evaluate(function (index, text) {
        var cell = IPython.notebook.get_cell(index);
        cell.set_text(text);
    }, index, text);
};

// Get the text content of a cell.
casper.get_cell_text = function(index){
    return this.evaluate(function (index) {
        var cell = IPython.notebook.get_cell(index);
        return cell.get_text();
    }, index);
};

// Inserts a cell at the bottom of the notebook
// Returns the new cell's index.
casper.insert_cell_at_bottom = function(cell_type){
    cell_type = cell_type || 'code';

    return this.evaluate(function (cell_type) {
        var cell = IPython.notebook.insert_cell_at_bottom(cell_type);
        return IPython.notebook.find_cell_index(cell);
    }, cell_type);
};

// Insert a cell at the bottom of the notebook and set the cells text.
// Returns the new cell's index.
casper.append_cell = function(text, cell_type) { 
    var index = this.insert_cell_at_bottom(cell_type);
    if (text !== undefined) {
        this.set_cell_text(index, text);
    }
    return index;
};

// Asynchronously executes a cell by index.
// Returns the cell's index.
casper.execute_cell = function(index){
    var that = this;
    this.then(function(){
        that.evaluate(function (index) {
            var cell = IPython.notebook.get_cell(index);
            cell.execute();
        }, index);
    });
    return index;
};

// Synchronously executes a cell by index.
// Optionally accepts a then_callback parameter.  then_callback will get called
// when the cell  has finished executing.
// Returns the cell's index.
casper.execute_cell_then = function(index, then_callback) {
    var return_val = this.execute_cell(index);

    this.wait_for_idle();

    var that = this;
    this.then(function(){ 
        if (then_callback!==undefined) {
            then_callback.apply(that, [index]);
        }
    });        

    return return_val;
};

// Utility function that allows us to easily check if an element exists 
// within a cell.  Uses JQuery selector to look for the element.
casper.cell_element_exists = function(index, selector){
    return casper.evaluate(function (index, selector) {
        var $cell = IPython.notebook.get_cell(index).element;
        return $cell.find(selector).length > 0;
    }, index, selector);
};

// Utility function that allows us to execute a jQuery function on an 
// element within a cell.
casper.cell_element_function = function(index, selector, function_name, function_args){
    return casper.evaluate(function (index, selector, function_name, function_args) {
        var $cell = IPython.notebook.get_cell(index).element;
        var $el = $cell.find(selector);
        return $el[function_name].apply($el, function_args);
    }, index, selector, function_name, function_args);
};


casper.select_cell = function(index) {
    this.evaluate(function (i) {
        IPython.notebook.select(i);
    }, {i: index});
};

casper.click_cell_editor = function(index) {
    // Code Mirror does not play nicely with emulated brower events.  
    // Instead of trying to emulate a click, here we run code similar to
    // the code used in Code Mirror that handles the mousedown event on a
    // region of codemirror that the user can focus.
    this.evaluate(function (i) {
        var cm = IPython.notebook.get_cell(i).code_mirror;
        if (cm.options.readOnly != "nocursor" && (document.activeElement != cm.display.input))
            cm.display.input.focus();
    }, {i: index});
};

casper.set_cell_editor_cursor = function(index, line_index, char_index) {
    // Set the Code Mirror instance cursor's location.
    this.evaluate(function (i, l, c) {
        IPython.notebook.get_cell(i).code_mirror.setCursor(l, c);
    }, {i: index, l: line_index, c: char_index});
};

casper.focus_notebook = function() {
    this.evaluate(function (){
        $('#notebook').focus();
    }, {});
};

casper.trigger_keydown = function() {
    for (var i = 0; i < arguments.length; i++) {
        this.evaluate(function (k) {
            IPython.keyboard.trigger_keydown(k);
        }, {k: arguments[i]});    
    }
};

casper.get_keyboard_mode = function() {
    return this.evaluate(function() {
        return IPython.keyboard_manager.mode;
    }, {});
};

casper.get_notebook_mode = function() {
    return this.evaluate(function() {
        return IPython.notebook.mode;
    }, {});
};

casper.get_cell = function(index) {
    return this.evaluate(function(i) {
        var cell = IPython.notebook.get_cell(i);
        if (cell) {
            return cell;
        }
        return null;
    }, {i : index});
};

casper.is_cell_editor_focused = function(index) {
    // Make sure a cell's editor is the only editor focused on the page.
    return this.evaluate(function(i) {
        var focused_textarea = $('#notebook .CodeMirror-focused textarea');
        if (focused_textarea.length > 1) { throw 'More than one Code Mirror editor is focused at once!'; }
        if (i === null) {
            return focused_textarea.length === 0;
        } else {
            var cell = IPython.notebook.get_cell(i);
            if (cell) {
                return cell.code_mirror.getInputField() == focused_textarea[0];
            }    
        }
        return false;
    }, {i : index});
};

casper.is_only_cell_selected = function(index) {
    return this.is_only_cell_on(index, 'selected', 'unselected');
};

casper.is_only_cell_edit = function(index) {
    return this.is_only_cell_on(index, 'edit_mode', 'command_mode');
};

casper.is_only_cell_on = function(i, on_class, off_class) {
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

casper.cell_has_class = function(index, classes) {
    return this.evaluate(function(i, c) {
        var cell = IPython.notebook.get_cell(i);
        if (cell) {
            return cell.element.hasClass(c);
        }
        return false;
    }, {i : index, c: classes});
};

// Wrap a notebook test to reduce boilerplate.
casper.notebook_test = function(test) {
    this.open_new_notebook();
    this.then(test);

    // Kill the kernel and delete the notebook.
    this.shutdown_current_kernel();
    // This is still broken but shouldn't be a problem for now.
    // this.delete_current_notebook();
    
    // This is required to clean up the page we just finished with. If we don't call this
    // casperjs will leak file descriptors of all the open WebSockets in that page. We
    // have to set this.page=null so that next time casper.start runs, it will create a
    // new page from scratch.
    this.then(function () {
        this.page.close();
        this.page = null;
    });
    
    // Run the browser automation.
    this.run(function() {
        this.test.done();
    });
};

casper.wait_for_dashboard = function () {
    // Wait for the dashboard list to load.
    casper.waitForSelector('.list_item');
}

casper.open_dashboard = function () {
    // Start casper by opening the dashboard page.
    var baseUrl = this.get_notebook_server();
    this.start(baseUrl);
    this.wait_for_dashboard();
}

casper.dashboard_test = function (test) {
    // Open the dashboard page and run a test.
    this.open_dashboard();
    this.then(test);

    this.then(function () {
        this.page.close();
        this.page = null;
    });
    
    // Run the browser automation.
    this.run(function() {
        this.test.done();
    });
}

casper.options.waitTimeout=10000
casper.on('waitFor.timeout', function onWaitForTimeout(timeout) {
    this.echo("Timeout for " + casper.get_notebook_server());
    this.echo("Is the notebook server running?");
});

// Pass `console.log` calls from page JS to casper.
casper.print_log = function () {
    this.on('remote.message', function(msg) {
        this.echo('Remote message caught: ' + msg);
    });
};
