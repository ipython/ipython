
//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {

    $('div#wrapper').addClass('vbox border-box-sizing')
    $('div.notebook').addClass('box-flex1 border-box-sizing')

    MathJax.Hub.Config({
        tex2jax: {
            inlineMath: [ ['$','$'], ["\\(","\\)"] ],
            displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
        },
        displayAlign: 'left', // Change this to 'center' to center equations.
        "HTML-CSS": {
            styles: {'.MathJax_Display': {"margin": 0}}
        }
    });

    IPython.notebook = new IPython.Notebook('div.notebook');
    IPython.notebook.insert_code_cell_after();

    $("#menu_tabs").tabs();

    $("#help_toolbar").buttonset();

    $("#kernel_toolbar").buttonset();
    $("#interrupt_kernel").click(function () {IPython.notebook.kernel.interrupt();});
    $("#restart_kernel").click(function () {IPython.notebook.kernel.restart();});
    $("#kernel_status").addClass("status_idle");

    $("#move_cell").buttonset();
    $("#move_up").button("option", "icons", {primary:"ui-icon-arrowthick-1-n"});
    $("#move_up").button("option", "text", false);
    $("#move_up").click(function () {IPython.notebook.move_cell_up();});
    $("#move_down").button("option", "icons", {primary:"ui-icon-arrowthick-1-s"});
    $("#move_down").button("option", "text", false);
    $("#move_down").click(function () {IPython.notebook.move_cell_down();});

    $("#insert_delete").buttonset();
    $("#insert_cell_before").click(function () {IPython.notebook.insert_code_cell_before();});
    $("#insert_cell_after").click(function () {IPython.notebook.insert_code_cell_after();});
    $("#delete_cell").button("option", "icons", {primary:"ui-icon-closethick"});
    $("#delete_cell").button("option", "text", false);
    $("#delete_cell").click(function () {IPython.notebook.delete_cell();});

    $("#cell_type").buttonset();
    $("#to_code").click(function () {IPython.notebook.text_to_code();});
    $("#to_text").click(function () {IPython.notebook.code_to_text();});

    $("#sort").buttonset();
    $("#sort_cells").click(function () {IPython.notebook.sort_cells();});

    $("#toggle").buttonset();
    $("#collapse").click(function () {IPython.notebook.collapse();});
    $("#expand").click(function () {IPython.notebook.expand();});

});

