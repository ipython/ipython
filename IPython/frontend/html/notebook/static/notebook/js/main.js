//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// On document ready
//============================================================================
"use strict";

// for the time beeing, we have to pass marked as a parameter here,
// as injecting require.js make marked not to put itself in the globals,
// which make both this file fail at setting marked configuration, and textcell.js
// which search marked into global.
require(['static/components/marked/lib/marked.js'],

function (marked) {

    window.marked = marked

    // monkey patch CM to be able to syntax highlight cell magics
    // bug reported upstream,
    // see https://github.com/marijnh/CodeMirror2/issues/670
    if(CodeMirror.getMode(1,'text/plain').indent == undefined ){
        console.log('patching CM for undefined indent');
        CodeMirror.modes.null = function() {
            return {token: function(stream) {stream.skipToEnd();},indent : function(){return 0}}
        }
    }

    CodeMirror.patchedGetMode = function(config, mode){
            var cmmode = CodeMirror.getMode(config, mode);
            if(cmmode.indent == null)
            {
                console.log('patch mode "' , mode, '" on the fly');
                cmmode.indent = function(){return 0};
            }
            return cmmode;
        }
    // end monkey patching CodeMirror

    IPython.mathjaxutils.init();

    IPython.read_only = $('body').data('readOnly') === 'True';
    $('#ipython-main-app').addClass('border-box-sizing');
    $('div#notebook_panel').addClass('border-box-sizing');
    // The header's bottom border is provided by the menu bar so we remove it.
    $('div#header').css('border-bottom-style','none');

    var baseProjectUrl = $('body').data('baseProjectUrl')

    IPython.page = new IPython.Page();
    IPython.layout_manager = new IPython.LayoutManager();
    IPython.pager = new IPython.Pager('div#pager', 'div#pager_splitter');
    IPython.quick_help = new IPython.QuickHelp();
    IPython.login_widget = new IPython.LoginWidget('span#login_widget',{baseProjectUrl:baseProjectUrl});
    IPython.notebook = new IPython.Notebook('div#notebook',{baseProjectUrl:baseProjectUrl, read_only:IPython.read_only});
    IPython.save_widget = new IPython.SaveWidget('span#save_widget');
    IPython.menubar = new IPython.MenuBar('#menubar',{baseProjectUrl:baseProjectUrl})
    IPython.toolbar = new IPython.MainToolBar('#maintoolbar')
    IPython.tooltip = new IPython.Tooltip()
    IPython.notification_area = new IPython.NotificationArea('#notification_area')
    IPython.notification_area.init_notification_widgets();

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
    var first_load = function () {
        IPython.layout_manager.do_resize();
        var hash = document.location.hash;
        if (hash) {
            document.location.hash = '';
            document.location.hash = hash;
        }
        IPython.notebook.set_autosave_interval(IPython.notebook.minimum_autosave_interval);
        // only do this once
        $([IPython.events]).off('notebook_loaded.Notebook', first_load);
    };

    $([IPython.events]).on('notebook_loaded.Notebook', first_load);
    IPython.notebook.load_notebook($('body').data('notebookId'));

    if (marked) {
        marked.setOptions({
            gfm : true,
            tables: true,
            langPrefix: "language-",
            highlight: function(code, lang) {
                var highlighted;
                try {
                    highlighted = hljs.highlight(lang, code, false);
                } catch(err) {
                    highlighted = hljs.highlightAuto(code);
                }
                return highlighted.value;
            }
        })
    }
}

);
