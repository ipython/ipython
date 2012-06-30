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

    IPython.init_mathjax();

    IPython.read_only = $('body').data('readOnly') === 'True';
    $('div#main_app').addClass('border-box-sizing ui-widget');
    $('div#notebook_panel').addClass('border-box-sizing ui-widget');
    // The header's bottom border is provided by the menu bar so we remove it.
    $('div#header').css('border-bottom-style','none');

    IPython.page = new IPython.Page();
    IPython.markdown_converter = new Markdown.Converter();
    IPython.layout_manager = new IPython.LayoutManager();
    IPython.pager = new IPython.Pager('div#pager', 'div#pager_splitter');
    IPython.quick_help = new IPython.QuickHelp('span#quick_help_area');
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');
    IPython.notebook = new IPython.Notebook('div#notebook');
    IPython.save_widget = new IPython.SaveWidget('span#save_widget');
    IPython.menubar = new IPython.MenuBar('#menubar')
    IPython.toolbar = new IPython.ToolBar('#toolbar')
    IPython.tooltip = new IPython.Tooltip()
    IPython.notification_widget = new IPython.NotificationWidget('#notification')

    IPython.layout_manager.do_resize();

    $('body').append('<div id="fonttest"><pre><span id="test1">x</span>'+
                     '<span id="test2" style="font-weight: bold;">x</span>'+
                     '<span id="test3" style="font-style: italic;">x</span></pre></div>')
    var nh = $('#test1').innerHeight();
    var bh = $('#test2').innerHeight();
    var ih = $('#test3').innerHeight();
    if(nh != bh || nh != ih) {
        $('head').append('<style>.CodeMirror span { vertical-align: bottom; }</style>');
    }
    $('#fonttest').remove();

    if(IPython.read_only){
        // hide various elements from read-only view
        $('div#pager').remove();
        $('div#pager_splitter').remove();

        // set the notebook name field as not modifiable
        $('#notebook_name').attr('disabled','disabled')
    }

    IPython.page.show();

    IPython.layout_manager.do_resize();
    $([IPython.events]).on('notebook_loaded.Notebook', function () {
        IPython.layout_manager.do_resize();
        IPython.save_widget.update_url();
    })
    IPython.notebook.load_notebook($('body').data('notebookId'));

});

