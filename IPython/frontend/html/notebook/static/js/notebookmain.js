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
    IPython.read_only = $('meta[name=read_only]').attr("content") == 'True';

    $('div#header').addClass('border-box-sizing');
    $('div#main_app').addClass('border-box-sizing ui-widget ui-widget-content');
    $('div#notebook_panel').addClass('border-box-sizing ui-widget');

    IPython.layout_manager = new IPython.LayoutManager();
    IPython.pager = new IPython.Pager('div#pager', 'div#pager_splitter');
    IPython.left_panel = new IPython.LeftPanel('div#left_panel', 'div#left_panel_splitter');
    IPython.save_widget = new IPython.SaveWidget('span#save_widget');
    IPython.quick_help = new IPython.QuickHelp('span#quick_help_area');
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');
    IPython.print_widget = new IPython.PrintWidget('span#print_widget');
    IPython.notebook = new IPython.Notebook('div#notebook');
    IPython.kernel_status_widget = new IPython.KernelStatusWidget('#kernel_status');
    IPython.kernel_status_widget.status_idle();

    IPython.layout_manager.do_resize();

    // These have display: none in the css file and are made visible here to prevent FLOUC.
    $('div#header').css('display','block');

    if(IPython.read_only){
        // hide various elements from read-only view
        IPython.save_widget.element.find('button#save_notebook').addClass('hidden');
        IPython.quick_help.element.addClass('hidden'); // shortcuts are disabled in read_only
        $('button#new_notebook').addClass('hidden');
        $('div#cell_section').addClass('hidden');
        $('div#kernel_section').addClass('hidden');
        $('span#login_widget').removeClass('hidden');
        // left panel starts collapsed, but the collapse must happen after
        // elements start drawing.  Don't draw contents of the panel until
        // after they are collapsed
        IPython.left_panel.left_panel_element.css('visibility', 'hidden');
    }

    $('div#main_app').css('display','block');

    // Perform these actions after the notebook has been loaded.
    // We wait 100 milliseconds because the notebook scrolls to the top after a load
    // is completed and we need to wait for that to mostly finish.
    IPython.notebook.load_notebook(function () {
        setTimeout(function () {
            IPython.save_widget.update_url();
            IPython.layout_manager.do_resize();
            IPython.pager.collapse();
            if(IPython.read_only){
                // collapse the left panel on read-only
                IPython.left_panel.collapse();
                // and finally unhide the panel contents after collapse
                setTimeout(function(){
                    IPython.left_panel.left_panel_element.css('visibility', 'visible');
                }, 200)
            }
        },100);
    });

});

