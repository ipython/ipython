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
