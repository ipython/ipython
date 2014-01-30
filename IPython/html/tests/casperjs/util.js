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
        // XXX: Kind of odd, the next line works for one test, but not when
        // running multiple tests back-to-back, so we will just point the main
        // casper browser to the same URL as the popup we just grabbed.

        //this.page = this.popups[0];
        this.open(this.popups[0].url);
    });

    // initially, the cells aren't created, so wait for them to appear
    this.waitForSelector('.CodeMirror-code');
    // and make sure the kernel has started
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

// return whether or not the kernel is running
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
};

// Delete created notebook.
casper.delete_current_notebook = function () {
    this.thenEvaluate(function() {
        var nbData = $('body').data();
        var url = nbData.baseProjectUrl + 'notebooks/' + nbData.notebookId;
        $.ajax(url, {
            type: 'DELETE',
        });
    });
};

casper.wait_for_idle = function () {
    this.then(function () {
        this.waitFor(function () {
            return this.evaluate(function () {
                return IPython._status == 'idle';
            });
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

// Inserts a cell at the bottom of the notebook
// Returns the new cell's index.
casper.insert_cell_at_bottom = function(cell_type){
    if (cell_type===undefined) {
        cell_type = 'code';
    }

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

// Wrap a notebook test to reduce boilerplate.
casper.notebook_test = function(test) {
    this.open_new_notebook();
    this.then(test);
    //XXX: we get sporadic error messages when shutting down some of the tests.
    //     Since the entire server will go down at the end of running the test
    //     suite, it's ok for now to not try to shut anything down.
    this.shutdown_current_kernel();
    
    //XXX: the implementation of delete_current_notebook is currently broken
    //     it's not a big deal, since the notebook directory will be deleted on
    //     cleanup, but we should add tests for deleting the notebook separately
    //this.delete_current_notebook();
    
    // Run the browser automation.
    this.run(function() {
        this.test.done();
    });
};

casper.options.waitTimeout=10000
casper.on('waitFor.timeout', function onWaitForTimeout(timeout) {
    this.echo("Timeout for " + casper.get_notebook_server());
    this.echo("Is the notebook server running?");
});

// Pass `console.log` calls from page JS to casper.
casper.printLog = function () {
    this.on('remote.message', function(msg) {
        this.echo('Remote message caught: ' + msg);
    });
};
