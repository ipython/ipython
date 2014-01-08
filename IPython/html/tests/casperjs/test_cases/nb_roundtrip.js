// Test opening a rich notebook, saving it, and reopening it again.
//
//toJSON fromJSON toJSON and do a string comparison


// this is just a copy of OutputArea.mime_mape_r in IPython/html/static/notebook/js/outputarea.js
mime =  {
        "text" : "text/plain",
        "html" : "text/html",
        "svg" : "image/svg+xml",
        "png" : "image/png",
        "jpeg" : "image/jpeg",
        "latex" : "text/latex",
        "json" : "application/json",
        "javascript" : "application/javascript",
    };
    
function assert_has(short_name, json, result, result2) {
    long_name = mime[short_name];
    this.test.assertTrue(result.hasOwnProperty(long_name),
            'toJSON()   original embeded JSON keeps ' + long_name);
    this.test.assertTrue(json[0].hasOwnProperty(short_name),
            'toJSON()   representation uses ' + short_name);
    this.test.assertTrue(result2.hasOwnProperty(long_name),
            'fromJSON() embeded ' + short_name + ' gets mime key ' + long_name);
}

casper.notebook_test(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        // "we have to make messes to find out who we are"
        cell.set_text([
            "%%javascript",
            "IPython.notebook.insert_cell_below('code')"
            ].join('\n')
            );

        cell.execute();
    });

    this.wait_for_output(0);

    this.then(function ( ) {
        var result = this.get_output_cell(0);
        var num_cells = this.get_cells_length();
        this.test.assertEquals(num_cells, 2, '%%javascript magic works');
        this.test.assertTrue(result.hasOwnProperty('application/javascript'),
            'JS embeded with mime key');
    });

    //this.thenEvaluate(function() { IPython.notebook.save_notebook(); });

    this.then(function ( ) {
        json = this.evaluate(function() {
            var json = IPython.notebook.get_cell(0).output_area.toJSON();
            // appended cell will initially be empty, lets add it some output
            var cell = IPython.notebook.get_cell(1).output_area.fromJSON(json);
            return json;
        });
        var result = this.get_output_cell(0);
        var result2 = this.get_output_cell(1);

        assert_has.apply(this, ['javascript', json, result, result2]);

    });

    this.then(function() {
        // test output of text/plain and application/json keys
        this.evaluate(function() {
            IPython.notebook.get_cell(0).clear_output();
            IPython.notebook.get_cell(1).clear_output();
        });
        this.set_cell_text(0, "%lsmagic");
        this.execute_cell(0);
    });
   
    this.then(function ( ) {
        json = this.evaluate(function() {
            var json = IPython.notebook.get_cell(0).output_area.toJSON();
            // appended cell will initially be empty, lets add it some output
            var cell = IPython.notebook.get_cell(1).output_area.fromJSON(json);
            return json;
        });
        var result = this.get_output_cell(0);
        var result2 = this.get_output_cell(1);
        this.test.assertEquals(result.output_type, 'pyout',
            'testing pyout application/json and text/plain');

        assert_has.apply(this, ['json', json, result, result2]);
        assert_has.apply(this, ['text', json, result, result2]);

    });
    this.then(function() {
        // test display of text/plain and application/json keys
        this.evaluate(function() {
            IPython.notebook.get_cell(0).clear_output();
            IPython.notebook.get_cell(1).clear_output();
        });
        this.set_cell_text(0,
            "x = %lsmagic\nfrom IPython.display import display; display(x)");
        this.execute_cell(0);
    });

    this.then(function ( ) {
        json = this.evaluate(function() {
            var json = IPython.notebook.get_cell(0).output_area.toJSON();
            // appended cell will initially be empty, lets add it some output
            var cell = IPython.notebook.get_cell(1).output_area.fromJSON(json);
            return json;
        });
        var result = this.get_output_cell(0);
        var result2 = this.get_output_cell(1);
        this.test.assertEquals(result.output_type, 'display_data',
            'testing display_data application/json and text/plain');
        
        assert_has.apply(this, ['json', json, result, result2]);
        assert_has.apply(this, ['text', json, result, result2]);

    });

});
