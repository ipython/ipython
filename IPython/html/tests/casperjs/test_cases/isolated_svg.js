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

        this.test.assertEquals(colors[0], '#ff0000', 'First svg should be red');
        this.test.assertEquals(colors[1], '#000000', 'Second svg should be black');
    });

    // now ensure that we can pass the same metadata dict to plain old display()
    this.thenEvaluate(function () {
        var cell = IPython.notebook.get_cell(0);
        cell.set_text( "from IPython.display import display\n"
                     + "display(SVG(s1), metadata=dict(isolated=True))\n"
                     + "display(SVG(s2), metadata=dict(isolated=True))\n"
            );
        cell.execute();
    });
   
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

        this.test.assertEquals(colors[0], '#ff0000', 'First svg should be red');
        this.test.assertEquals(colors[1], '#000000', 'Second svg should be black');
    });
});
