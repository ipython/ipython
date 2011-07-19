
//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {


    $('div#notebook_app').addClass('border-box-sizing ui-widget ui-widget-content');
    $('div#left_panel').addClass('border-box-sizing ui-widget');
    $('div#left_panel_splitter').addClass('border-box-sizing ui-widget ui-state-default');
    $('div#notebook_panel').addClass('border-box-sizing ui-widget');
    $('div#notebook').addClass('border-box-sizing');

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

    var do_resize = function () {
        var win = $(window);
        var w = win.width();
        var h = win.height();
        var header_height = $('div#header').outerHeight(true);
        var app_height = h - header_height - 2;
        var pager_height = $('div#pager').outerHeight(true);
        var pager_splitter_height = $('div#pager_splitter').outerHeight(true);
        $('div#notebook_app').height(app_height + 2);
        $('div#left_panel').height(app_height);
        $('div#left_panel_splitter').height(app_height);
        $('div#notebook_panel').height(app_height);
        $('div#notebook').height(app_height-pager_height-pager_splitter_height);
        console.log('resize: ', app_height);
    };

    $(window).resize(do_resize);

    IPython.notebook = new IPython.Notebook('div#notebook');
    IPython.notebook.insert_code_cell_after();

    IPython.pager = new IPython.Pager('div#pager', 'div#pager_splitter');

    do_resize();

//    $("#menu_tabs").tabs();

//    $("#help_toolbar").buttonset();

//    $("#kernel_toolbar").buttonset();
//    $("#interrupt_kernel").click(function () {IPython.notebook.kernel.interrupt();});
//    $("#restart_kernel").click(function () {IPython.notebook.kernel.restart();});
//    $("#kernel_status").addClass("status_idle");

//    $("#move_cell").buttonset();
//    $("#move_up").button("option", "icons", {primary:"ui-icon-arrowthick-1-n"});
//    $("#move_up").button("option", "text", false);
//    $("#move_up").click(function () {IPython.notebook.move_cell_up();});
//    $("#move_down").button("option", "icons", {primary:"ui-icon-arrowthick-1-s"});
//    $("#move_down").button("option", "text", false);
//    $("#move_down").click(function () {IPython.notebook.move_cell_down();});

//    $("#insert_delete").buttonset();
//    $("#insert_cell_before").click(function () {IPython.notebook.insert_code_cell_before();});
//    $("#insert_cell_after").click(function () {IPython.notebook.insert_code_cell_after();});
//    $("#delete_cell").button("option", "icons", {primary:"ui-icon-closethick"});
//    $("#delete_cell").button("option", "text", false);
//    $("#delete_cell").click(function () {IPython.notebook.delete_cell();});

//    $("#cell_type").buttonset();
//    $("#to_code").click(function () {IPython.notebook.text_to_code();});
//    $("#to_text").click(function () {IPython.notebook.code_to_text();});

//    $("#sort").buttonset();
//    $("#sort_cells").click(function () {IPython.notebook.sort_cells();});

//    $("#toggle").buttonset();
//    $("#collapse").click(function () {IPython.notebook.collapse();});
//    $("#expand").click(function () {IPython.notebook.expand();});

});

