//
// Utility functions for the HTML notebook's CasperJS tests.
//

// Get the URL of a notebook server on which to run tests.
casper.getNotebookServer = function () {
    return 'http://127.0.0.1:' + casper.cli.get("port");
};

// Create and open a new notebook.
casper.openNewNotebook = function () {
    var baseUrl = this.getNotebookServer();
    this.start(baseUrl + '/new');
    // initially, the cells aren't created, so wait for them to appear
    this.waitForSelector('.CodeMirror-code');
};

// Shut down the current notebook's kernel.
casper.shutdownCurrentKernel = function () {
    this.thenEvaluate(function() {
        IPython.notebook.kernel.kill();
    });
};

// Delete created notebook.
casper.deleteCurrentNotebook = function () {
    this.thenEvaluate(function() {
        var nbData = $('body').data();
        var url = nbData.baseProjectUrl + 'notebooks/' + nbData.notebookId;
        $.ajax(url, {
            type: 'DELETE',
        });
    });
};

// Wrap a notebook test to reduce boilerplate.
casper.notebookTest = function(test) {
    this.openNewNotebook();
    this.then(test);
    this.shutdownCurrentKernel();
    //XXX: the implementation of deleteCurrentNotebook is currently broken
    // it's not a big deal, since the notebook directory will be deleted on
    // cleanup, but we should add tests for deleting the notebook separately
    //this.deleteCurrentNotebook();
    
    // Run the browser automation.
    this.run(function() {
        this.test.done();
    });
};

// Pass `console.log` calls from page JS to casper.
casper.printLog = function () {
    this.on('remote.message', function(msg) {
        this.echo('Remote message caught: ' + msg);
    });
};
