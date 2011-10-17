//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {

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
    IPython.markdown_converter = new Markdown.Converter();

    $('div#header').addClass('border-box-sizing');
    $('div#main_app').addClass('border-box-sizing ui-widget ui-widget-content');
    $('div#notebook_panel').addClass('border-box-sizing ui-widget');

    IPython.layout_manager = new IPython.LayoutManager();
    IPython.pager = new IPython.Pager('div#pager', 'div#pager_splitter');
    IPython.left_panel = new IPython.LeftPanel('div#left_panel', 'div#left_panel_splitter');
    IPython.save_widget = new IPython.SaveWidget('span#save_widget');
    IPython.quick_help = new IPython.QuickHelp('span#quick_help_area');
    IPython.print_widget = new IPython.PrintWidget('span#print_widget');
    IPython.notebook = new IPython.Notebook('div#notebook');
    IPython.kernel_status_widget = new IPython.KernelStatusWidget('#kernel_status');
    IPython.kernel_status_widget.status_idle();

    IPython.layout_manager.do_resize();

    // These have display: none in the css file and are made visible here to prevent FLOUC.
    $('div#header').css('display','block');
    $('div#main_app').css('display','block');

    // Perform these actions after the notebook has been loaded.
    // We wait 100 milliseconds because the notebook scrolls to the top after a load
    // is completed and we need to wait for that to mostly finish.
    IPython.notebook.load_notebook(function () {
        setTimeout(function () {
            IPython.save_widget.update_url();
            IPython.layout_manager.do_resize();
            IPython.pager.collapse();
        },100);
    });

});

