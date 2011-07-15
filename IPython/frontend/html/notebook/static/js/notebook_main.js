
//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {

    $('div#wrapper').addClass('vbox border-box-sizing')
    $('div#notebook_app').addClass('hbox box-flex1 border-box-sizing')
    $('div#left_panel').addClass('vbox border-box-sizing ui-widget ui-widget-content')
    $('div#pager_splitter').addClass('border-box-sizing ui-widget ui-widget-header')
    $('div#notebook_panel').addClass('vbox box-flex1 border-box-sizing ui-widget ui-widget-content')
    $('div#notebook').addClass('vbox box-flex1 border-box-sizing')
    $('div#left_panel_splitter').addClass('border-box-sizing ui-widget ui-widget-header')
    $('div#pager').addClass('border-box-sizing')

    $('div#pager_splitter').click(function () {
        $('div#pager').toggle('fast');
    });

    $('div#pager_splitter').hover(
        function () {
            $('div#pager_splitter').addClass('ui-state-hover');
        },
        function () {
            $('div#pager_splitter').removeClass('ui-state-hover');
        }
    );

    $('div#pager').hide();

    $('div#left_panel_splitter').click(function () {
        $('div#left_panel').toggle('fast');
    });

    $('div#left_panel_splitter').hover(
        function () {
            $('div#left_panel_splitter').addClass('ui-state-hover');
        },
        function () {
            $('div#left_panel_splitter').removeClass('ui-state-hover');
        }
    );

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

    IPython.notebook = new IPython.Notebook('div#notebook');
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

