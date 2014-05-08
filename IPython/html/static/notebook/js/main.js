//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// On document ready
//============================================================================

// for the time beeing, we have to pass marked as a parameter here,
// as injecting require.js make marked not to put itself in the globals,
// which make both this file fail at setting marked configuration, and textcell.js
// which search marked into global.
require(['components/marked/lib/marked',
         'widgets/js/init',
         'components/bootstrap-tour/build/js/bootstrap-tour.min'],

function (marked) {
    "use strict";

    window.marked = marked;

    // monkey patch CM to be able to syntax highlight cell magics
    // bug reported upstream,
    // see https://github.com/marijnh/CodeMirror2/issues/670
    if(CodeMirror.getMode(1,'text/plain').indent === undefined ){
        console.log('patching CM for undefined indent');
        CodeMirror.modes.null = function() {
            return {token: function(stream) {stream.skipToEnd();},indent : function(){return 0;}};
        };
    }

    CodeMirror.patchedGetMode = function(config, mode){
            var cmmode = CodeMirror.getMode(config, mode);
            if(cmmode.indent === null) {
                console.log('patch mode "' , mode, '" on the fly');
                cmmode.indent = function(){return 0;};
            }
            return cmmode;
        };
    // end monkey patching CodeMirror

    IPython.mathjaxutils.init();

    $('#ipython-main-app').addClass('border-box-sizing');
    $('div#notebook_panel').addClass('border-box-sizing');

    var opts = {
        base_url : IPython.utils.get_body_data("baseUrl"),
        notebook_path : IPython.utils.get_body_data("notebookPath"),
        notebook_name : IPython.utils.get_body_data('notebookName')
    };

    IPython.page = new IPython.Page();
    IPython.layout_manager = new IPython.LayoutManager();
    IPython.pager = new IPython.Pager('div#pager', 'div#pager_splitter');
    IPython.quick_help = new IPython.QuickHelp();
    try {
        IPython.tour = new IPython.NotebookTour();
    } catch (e) {
        console.log("Failed to instantiate Notebook Tour", e);
    }
    IPython.login_widget = new IPython.LoginWidget('span#login_widget', opts);
    IPython.notebook = new IPython.Notebook('div#notebook', opts);
    IPython.keyboard_manager = new IPython.KeyboardManager();
    IPython.save_widget = new IPython.SaveWidget('span#save_widget');
    IPython.menubar = new IPython.MenuBar('#menubar', opts);
    IPython.toolbar = new IPython.MainToolBar('#maintoolbar-container');
    IPython.tooltip = new IPython.Tooltip();
    IPython.notification_area = new IPython.NotificationArea('#notification_area');
    IPython.notification_area.init_notification_widgets();

    IPython.layout_manager.do_resize();

    $('body').append('<div id="fonttest"><pre><span id="test1">x</span>'+
                     '<span id="test2" style="font-weight: bold;">x</span>'+
                     '<span id="test3" style="font-style: italic;">x</span></pre></div>');
    var nh = $('#test1').innerHeight();
    var bh = $('#test2').innerHeight();
    var ih = $('#test3').innerHeight();
    if(nh != bh || nh != ih) {
        $('head').append('<style>.CodeMirror span { vertical-align: bottom; }</style>');
    }
    $('#fonttest').remove();

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
    $([IPython.events]).trigger('app_initialized.NotebookApp');
    IPython.notebook.load_notebook(opts.notebook_name, opts.notebook_path);

    if (marked) {
        marked.setOptions({
            gfm : true,
            tables: true,
            langPrefix: "language-",
            highlight: function(code, lang) {
                if (!lang) {
                    // no language, no highlight
                    return code;
                }
                var highlighted;
                try {
                    highlighted = hljs.highlight(lang, code, false);
                } catch(err) {
                    highlighted = hljs.highlightAuto(code);
                }
                return highlighted.value;
            }
        });
    }
});
