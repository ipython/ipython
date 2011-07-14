
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

    IPYTHON.notebook = new Notebook('div.notebook');
    IPYTHON.notebook.insert_code_cell_after();

    $("#menu_tabs").tabs();

    $("#help_toolbar").buttonset();

    $("#kernel_toolbar").buttonset();
    $("#interrupt_kernel").click(function () {IPYTHON.notebook.kernel.interrupt();});
    $("#restart_kernel").click(function () {IPYTHON.notebook.kernel.restart();});
    $("#kernel_status").addClass("status_idle");

    $("#move_cell").buttonset();
    $("#move_up").button("option", "icons", {primary:"ui-icon-arrowthick-1-n"});
    $("#move_up").button("option", "text", false);
    $("#move_up").click(function () {IPYTHON.notebook.move_cell_up();});
    $("#move_down").button("option", "icons", {primary:"ui-icon-arrowthick-1-s"});
    $("#move_down").button("option", "text", false);
    $("#move_down").click(function () {IPYTHON.notebook.move_cell_down();});

    $("#insert_delete").buttonset();
    $("#insert_cell_before").click(function () {IPYTHON.notebook.insert_code_cell_before();});
    $("#insert_cell_after").click(function () {IPYTHON.notebook.insert_code_cell_after();});
    $("#delete_cell").button("option", "icons", {primary:"ui-icon-closethick"});
    $("#delete_cell").button("option", "text", false);
    $("#delete_cell").click(function () {IPYTHON.notebook.delete_cell();});

    $("#cell_type").buttonset();
    $("#to_code").click(function () {IPYTHON.notebook.text_to_code();});
    $("#to_text").click(function () {IPYTHON.notebook.code_to_text();});

    $("#sort").buttonset();
    $("#sort_cells").click(function () {IPYTHON.notebook.sort_cells();});

    $("#toggle").buttonset();
    $("#collapse").click(function () {IPYTHON.notebook.collapse();});
    $("#expand").click(function () {IPYTHON.notebook.expand();});

});

