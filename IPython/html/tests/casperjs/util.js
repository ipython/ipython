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

    this.then(function () {
        // XXX: Kind of odd, the next line works for one test, but not when
        // running multiple tests back-to-back, so we will just point the main
        // casper browser to the same URL as the popup we just grabbed.

        //this.page = this.popups[0];
        this.open(this.popups[0].url);
    });

    // initially, the cells aren't created, so wait for them to appear
    this.waitForSelector('.CodeMirror-code');
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

casper.options.waitTimeout=5000
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
