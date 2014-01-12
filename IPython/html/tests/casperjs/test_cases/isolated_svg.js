//
// Test display isolation
// An object whose metadata contains an "isolated" tag must be isolated
// from the rest of the document. In the case of inline SVGs, this means
// that multiple SVGs have different scopes. This test checks that there
// are no CSS leaks between two isolated SVGs.
//

casper.notebook_test(function () {
    this.evaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text( "from IPython.core.display import SVG, display_svg\n"
                     + "s1 = '''<svg width='1cm' height='1cm' viewBox='0 0 1000 500'>"
                     + "<defs><style>rect {fill:red;}; </style></defs>"
                     + "<rect id='r1' x='200' y='100' width='600' height='300' /></svg>"
                     + "'''\n"
                     + "s2 = '''<svg width='1cm' height='1cm' viewBox='0 0 1000 500'>"
                     + "<rect id='r2' x='200' y='100' width='600' height='300' /></svg>"
                     + "'''\n"
                     + "display_svg(SVG(s1), metadata=dict(isolated=True))\n"
                     + "display_svg(SVG(s2), metadata=dict(isolated=True))\n"
            );
        cell.execute();
        console.log("hello" );
    });

    this.then(function() {
        var fname=this.test.currentTestFile.split('/').pop().toLowerCase();
        this.echo(fname)
        this.echo(this.currentUrl)
        this.evaluate(function (n) {
            IPython.notebook.rename(n);
            console.write("hello" + n);
            IPython.notebook.save_notebook();
        }, {n : fname});
        this.echo(this.currentUrl)
    });

    this.then(function() {
    
        url = this.evaluate(function() {
            IPython.notebook.rename("foo");
            //$("span#notebook_name")[0].click();
            //$("input")[0].value = "please-work";
            //$(".btn-primary")[0].click();
            return document.location.href;
        })
        this.echo("renamed" + url);
        this.echo(this.currentUrl);
    });

    this.wait_for_output(0);

    this.then(function () {
        var colors = this.evaluate(function () {
            var colors = [];
            var ifr = __utils__.findAll("iframe");
            var svg1 = ifr[0].contentWindow.document.getElementById('r1');
            colors[0] = window.getComputedStyle(svg1)["fill"];
            var svg2 = ifr[1].contentWindow.document.getElementById('r2');
            colors[1] = window.getComputedStyle(svg2)["fill"];
            return colors;
        });

        this.test.assertEquals(colors && colors[0], '#ff0000', 'display_svg() First svg should be red');
        this.test.assertEquals(colors && colors[1], '#000000', 'display_svg() Second svg should be black');
    });

    // now ensure that we can pass the same metadata dict to plain old display()
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.clear_output();
        cell.set_text( "from IPython.display import display\n"
                     + "display(SVG(s1), metadata=dict(isolated=True))\n"
                     + "display(SVG(s2), metadata=dict(isolated=True))\n"
            );
        cell.execute();
    });

    this.wait_for_output(0);

    // same test as original
    this.then(function () {
        var colors = this.evaluate(function () {
            var colors = [];
            var ifr = __utils__.findAll("iframe");
            var svg1 = ifr[0].contentWindow.document.getElementById('r1');
            colors[0] = window.getComputedStyle(svg1)["fill"];
            var svg2 = ifr[1].contentWindow.document.getElementById('r2');
            colors[1] = window.getComputedStyle(svg2)["fill"];
            return colors;
        });

        this.test.assertEquals(colors && colors[0], '#ff0000', 'display() First svg should be red');
        this.test.assertEquals(colors && colors[1], '#000000', 'display() Second svg should be black');
    });
});
