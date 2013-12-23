// Test opening a rich notebook, saving it, and reopening it again.
//
//toJSON fromJSON toJSON and do a string comparison
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
        this.test.assertTrue(result.hasOwnProperty('application/javascript'),
            'toJSON() original embeded JS keeps mime key');
        this.test.assertTrue(json[0].hasOwnProperty('javascript'),
            'toJSON() representation uses short key');
        this.test.assertTrue(result2.hasOwnProperty('application/javascript'),
            'fromJSON() embeded JS gets mime key');

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
        this.test.assertTrue(result.hasOwnProperty('application/json'),
            'toJSON() original embeded JSON keeps mime key');
        this.test.assertTrue(json[0].hasOwnProperty('json'),
            'toJSON() representation uses short key');
        this.test.assertTrue(result2.hasOwnProperty('application/json'),
            'fromJSON() embeded JS gets mime key');

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
        this.test.assertTrue(result.hasOwnProperty('text/plain'),
            'toJSON()\t original embeded text keeps mime key');
        this.test.assertTrue(json[0].hasOwnProperty('text'),
            'toJSON()\t representation uses short key');
        this.test.assertTrue(result2.hasOwnProperty('text/plain'),
            'fromJSON()\t embeded text gets mime key');

    });


    //this.thenEvaluate(function () {
    //var cell = IPython.notebook.get_cell(0);

    //    // we have to make messes to find out who we are
    //    cell.set_text([
    //        "import IPython.html.tests as t",
    //        "t.write_test_notebook('rich_output.ipynb')"
    //        ].join('\n')
    //        );

    //    cell.execute();
    //});
    //
    //this.wait_for_output(0);

});
