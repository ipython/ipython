// Test opening a rich notebook, saving it, and reopening it again.
//
//toJSON fromJSON toJSON and do a string comparison
casper.notebook_test(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        // "we have to make messes to find out who we are"
        cell.set_text([
            "%%javascript",
            "IPython.notebook.insert_cell_above('code')"
            ].join('\n')
            );

        cell.execute();
    });
    
    this.wait_for_output(0);

    this.then(function ( ) {
        var result = this.get_output_cell(1);
        var num_cells = this.get_cells_length();
        this.test.assertEquals(num_cells, 2, '%%javascript magic works');
        this.test.assertTrue(result.hasOwnProperty('application/javascript'), 'JS embeded with mime key');
    });


    //this.thenEvaluate(function () { var cell = IPython.notebook.get_cell(0);

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

    //this.then(function ( ) {
    //    var result = this.get_output_cell(0);
    //    var num_cells = this.get_cells_length();
    //    this.test.assertEquals(result.text, '10\n', 'opening notebook JSON');
    //    this.test.assertEquals(num_cells, 2, '              %%javascript magic works')
    //});

});
