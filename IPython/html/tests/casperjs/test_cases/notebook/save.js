//
// Test saving a notebook with escaped characters
//

casper.notebook_test(function () {
    // don't use unicode with ambiguous composed/decomposed normalization
    // because the filesystem may use a different normalization than literals.
    // This causes no actual problems, but will break string comparison.
    var nbname = "has#hash and space and unicø∂e.ipynb";
    
    this.evaluate(function (nbname) {
        IPython.notebook.notebook_name = nbname;
        IPython._save_success = IPython._save_failed = false;
        $([IPython.events]).on('notebook_saved.Notebook', function () {
            IPython._save_success = true;
        });
        $([IPython.events]).on('notebook_save_failed.Notebook',
            function (event, xhr, status, error) {
                IPython._save_failed = "save failed with " + xhr.status + xhr.responseText;
        });
        IPython.notebook.save_notebook();
    }, {nbname:nbname});
    
    this.waitFor(function () {
        return this.evaluate(function(){
            return IPython._save_failed || IPython._save_success;
        });
    });
    
    this.then(function(){
        var success_failure = this.evaluate(function(){
            return [IPython._save_success, IPython._save_failed];
        });
        this.test.assertEquals(success_failure[1], false, "Save did not fail");
        this.test.assertEquals(success_failure[0], true, "Save OK");
        
        var current_name = this.evaluate(function(){
            return IPython.notebook.notebook_name;
        });
        this.test.assertEquals(current_name, nbname, "Save with complicated name");
    });
    
    this.thenEvaluate(function(){
        $([IPython.events]).on('checkpoint_created.Notebook', function (evt, data) {
            IPython._checkpoint_created = true;
        });
        IPython._checkpoint_created = false;
        IPython.notebook.save_checkpoint();
    });
    
    this.waitFor(function () {
        return this.evaluate(function(){
            return IPython._checkpoint_created;
        });
    });
    
    this.then(function(){
        var checkpoints = this.evaluate(function(){
            return IPython.notebook.checkpoints;
        });
        this.test.assertEquals(checkpoints.length, 1, "checkpoints OK");
    });

    this.then(function(){
        var baseUrl = this.get_notebook_server();
        this.open(baseUrl);
    });

    this.waitForSelector('.list_item');
    
    this.then(function(){
        var notebook_url = this.evaluate(function(nbname){
            var escaped_name = encodeURIComponent(nbname);
            var return_this_thing;
            $("a.item_link").map(function (i,a) {
                if (a.href.indexOf(escaped_name) >= 0) {
                    return_this_thing = a.href;
                    return;
                }
            });
            return return_this_thing;
        }, {nbname:nbname});
        this.test.assertEquals(notebook_url == null, false, "Escaped URL in notebook list");
        // open the notebook
        this.open(notebook_url);
    });
    
    // wait for the notebook
    this.waitForSelector("#notebook");
    
    this.waitFor(function(){
        return this.evaluate(function(){
            return IPython.notebook || false;
        });
    });
    
    this.then(function(){
        // check that the notebook name is correct
        var notebook_name = this.evaluate(function(){
            return IPython.notebook.notebook_name;
        });
        this.test.assertEquals(notebook_name, nbname, "Notebook name is correct");
    });
    
});
