//
// Various output tests
//

casper.notebook_test(function () {
    
    this.test_coalesced_output = function (msg, code, expected) {
        this.then(function () {
            this.echo("Test coalesced output: " + msg);
        });
        
        this.thenEvaluate(function (code) {
            IPython.notebook.insert_cell_at_index("code", 0);
            var cell = IPython.notebook.get_cell(0);
            cell.set_text(code);
            cell.execute();
        }, {code: code});
        
        this.wait_for_output(0);
        
        this.then(function () {
            var results = this.evaluate(function () {
                var cell = IPython.notebook.get_cell(0);
                return cell.output_area.outputs;
            });
            this.test.assertEquals(results.length, expected.length, "correct number of outputs");
            for (var i = 0; i < results.length; i++) {
                var r = results[i];
                var ex = expected[i];
                this.test.assertEquals(r.output_type, ex.output_type, "output  " + i);
                if (r.output_type === 'stream') {
                    this.test.assertEquals(r.name, ex.name, "stream  " + i);
                    this.test.assertEquals(r.text, ex.text, "content " + i);
                }
            }
        });
        
    };
    
    this.thenEvaluate(function () {
        IPython.notebook.insert_cell_at_index("code", 0);
        var cell = IPython.notebook.get_cell(0);
        cell.set_text([
            "from __future__ import print_function",
            "import sys",
            "from IPython.display import display"
            ].join("\n")
        );
        cell.execute();
    });
    
    this.test_coalesced_output("stdout", [
        "print(1)",
        "sys.stdout.flush()",
        "print(2)",
        "sys.stdout.flush()",
        "print(3)"
        ].join("\n"), [{
            output_type: "stream",
            name: "stdout",
            text: "1\n2\n3\n"
        }]
    );
    
    this.test_coalesced_output("stdout+sdterr", [
        "print(1)",
        "sys.stdout.flush()",
        "print(2)",
        "print(3, file=sys.stderr)"
        ].join("\n"), [{
            output_type: "stream",
            name: "stdout",
            text: "1\n2\n"
        },{
            output_type: "stream",
            name: "stderr",
            text: "3\n"
        }]
    );

    this.test_coalesced_output("display splits streams", [
        "print(1)",
        "sys.stdout.flush()",
        "display(2)",
        "print(3)"
        ].join("\n"), [{
            output_type: "stream",
            name: "stdout",
            text: "1\n"
        },{
            output_type: "display_data",
        },{
            output_type: "stream",
            name: "stdout",
            text: "3\n"
        }]
    );
});
