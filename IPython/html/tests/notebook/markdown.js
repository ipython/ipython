//
// Test that a Markdown cell is rendered to HTML.
//
casper.notebook_test(function () {
    "use strict";
    // Test JavaScript models.
    var output = this.evaluate(function () {
        IPython.notebook.to_markdown();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('# Foo');
        cell.render();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<h1 id=\"Foo\">Foo<a class=\"anchor-link\" href=\"#Foo\">¶</a></h1>', 'Markdown JS API works.');
    
    // Test menubar entries.
    output = this.evaluate(function () {
        $('#to_code').mouseenter().click();
        $('#to_markdown').mouseenter().click();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('**Bar**');
        $('#run_cell').mouseenter().click();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<p><strong>Bar</strong></p>', 'Markdown menubar items work.');
    
    // Test toolbar buttons.
    output = this.evaluate(function () {
        $('#cell_type').val('code').change();
        $('#cell_type').val('markdown').change();
        var cell = IPython.notebook.get_selected_cell();
        cell.set_text('*Baz*');
        $("button[data-jupyter-action='ipython.run-select-next']")[0].click();
        return cell.get_rendered();
    });
    this.test.assertEquals(output.trim(), '<p><em>Baz</em></p>', 'Markdown toolbar items work.');
    
    // Test markdown headings

    var text = 'multi\nline';

    this.evaluate(function (text) {
        var cell = IPython.notebook.insert_cell_at_index('markdown', 0);
        cell.set_text(text);
    }, {text: text});

    var set_level = function (level) {
        return casper.evaluate(function (level) {
            var cell = IPython.notebook.get_cell(0);
            cell.set_heading_level(level);
            return cell.get_text();
        }, {level: level});
    };
    
    var level_text;
    var levels = [ 1, 2, 3, 4, 5, 6, 2, 1 ];
    for (var idx=0; idx < levels.length; idx++) {
        var level = levels[idx];
        level_text = set_level(level);
        var hashes = new Array(level + 1).join('#');
        this.test.assertEquals(level_text, hashes + ' ' + text, 'markdown set_heading_level ' + level);
    }
});
