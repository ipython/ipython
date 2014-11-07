//
// Test saving a notebook with escaped characters
//

casper.notebook_test(function () {
    // don't use unicode with ambiguous composed/decomposed normalization
    // because the filesystem may use a different normalization than literals.
    // This causes no actual problems, but will break string comparison.
    var nbname = "has#hash and space and unicø∂e.ipynb";
    
    this.append_cell("s = '??'", 'code');
    
    this.thenEvaluate(function (nbname) {
        require(['base/js/events'], function (events) {
            IPython.notebook.set_notebook_name(nbname);
            IPython._save_success = IPython._save_failed = false;
            events.on('notebook_saved.Notebook', function () {
                IPython._save_success = true;
            });
            events.on('notebook_save_failed.Notebook',
                function (event, error) {
                    IPython._save_failed = "save failed with " + error;
            });
            IPython.notebook.save_notebook();
        });
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
        var current_path = this.evaluate(function(){
            return IPython.notebook.notebook_path;
        });
        this.test.assertEquals(current_path, nbname, "path OK");
    });
    
    this.thenEvaluate(function(){
        IPython._checkpoint_created = false;
        require(['base/js/events'], function (events) {
            events.on('checkpoint_created.Notebook', function (evt, data) {
                IPython._checkpoint_created = true;
            });
        });
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
        this.open_dashboard();
    });
    
    this.then(function(){
        var notebook_url = this.evaluate(function(nbname){
            var escaped_name = encodeURIComponent(nbname);
            var return_this_thing = null;
            $("a.item_link").map(function (i,a) {
                if (a.href.indexOf(escaped_name) >= 0) {
                    return_this_thing = a.href;
                    return;
                }
            });
            return return_this_thing;
        }, {nbname:nbname});
        this.test.assertNotEquals(notebook_url, null, "Escaped URL in notebook list");
        // open the notebook
        this.open(notebook_url);
    });
    
    // wait for the notebook
    this.waitFor(this.kernel_running);
    
    this.waitFor(function() {
        return this.evaluate(function () {
            return IPython && IPython.notebook && true;
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
