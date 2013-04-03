//
// Utility functions for the HTML notebook's CasperJS tests.
//

// Get the URL of a notebook server on which to run tests.
casper.getNotebookServer = function () {
    return 'http://127.0.0.1:8888';
};

// Create and open a new notebook.
casper.openNewNotebook = function () {
    var baseUrl = this.getNotebookServer();
    this.start(baseUrl + '/new');
};

// Shut down the current notebook's kernel.
casper.shutdownCurrentKernel = function () {
    this.thenEvaluate(function() {
        var baseUrl = $('body').data('baseProjectUrl');
        var kernelId = IPython.notebook.kernel.kernel_id;
        var url = baseUrl  + 'kernels/' + kernelId;
        $.ajax(url, {
            type: 'DELETE',
        });
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
    this.deleteCurrentNotebook();
    
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
