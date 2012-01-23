//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MenuBar
//============================================================================

var IPython = (function (IPython) {

    var FullEditWidget = function (selector) {
        this.selector = selector;
        this.opened = false;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    FullEditWidget.prototype.style = function () {
        var that = this;
        this.element.find('#close_fulledit').button().on('click', function (){
            that.close();
        })
        this.element.find('#fulledit_header').addClass('ui-widget ui-widget-header');
        this.element.find('#fulledit_editor').addClass('ui-widget ui-widget-content');
        this.ace_editor = ace.edit("fulledit_editor");
        this.ace_editor.setTheme("ace/theme/textmate");
        var PythonMode = require("ace/mode/python").Mode;
        this.ace_editor.getSession().setMode(new PythonMode());
        this.ace_editor.getSession().setTabSize(4);
        this.ace_editor.getSession().setUseSoftTabs(true);
        this.ace_editor.setHighlightActiveLine(false);
        // Ace sets its css dynamically, so we need to do this here. These
        // values are chosen to match those of our CodeMirror editors.
        $('.ace_editor').css({fontFamily: 'monospace', fontSize: '110%',
        lineHeight: '1.231'});
    };


    FullEditWidget.prototype.bind_events = function () {

    };


    FullEditWidget.prototype.open = function () {
        var cell = IPython.notebook.get_selected_cell();
        if (!this.opened) {
            $('#fulledit_widget').show();
            $('#main_app').hide();
            $('#menubar').hide();
            $('body').css({overflow : 'auto'});
            var code = cell.get_text();
            this.ace_editor.getSession().setValue(code);
            if (cell instanceof IPython.CodeCell) {
                var PythonMode = require("ace/mode/python").Mode;
                this.ace_editor.getSession().setMode(new PythonMode());
            } else if (cell instanceof IPython.MarkdownCell) {
                var MarkdownMode = require("ace/mode/markdown").Mode;
                this.ace_editor.getSession().setMode(new MarkdownMode());
            } else if (cell instanceof IPython.HTMLCell) {
                var HTMLMode = require("ace/mode/html").Mode;
                this.ace_editor.getSession().setMode(new HTMLMode());
            };
            this.ace_editor.focus();
            // On Safari (and Chrome/FF on Linux) the editor doesn't get
            // focus unless there is a window resize. For now, we trigger it
            // by hand until the bug is fixed upstream.
            window.resizeBy(0,1);
            window.resizeBy(0,-1);
            this.opened = true;
        };
    };


    FullEditWidget.prototype.close = function () {
        if (this.opened) {
            $('#fulledit_widget').hide();
            $('#main_app').show();
            //  We may need to add a refresh to all CM based cells after
            // showing them.
            $('#menubar').show();
            $('body').css({overflow : 'hidden'});
            var code = this.ace_editor.getSession().getValue();
            var cell = IPython.notebook.get_selected_cell();
            if (cell instanceof IPython.CodeCell) {
                cell.code_mirror.refresh();
                cell.set_text(code);                
            } else if (cell instanceof IPython.MarkdownCell || cell instanceof IPython.HTMLCell) {
                cell.edit();
                // If the cell was already in edit mode, we need to refresh/focus.
                cell.code_mirror.refresh();
                cell.code_mirror.focus();
                cell.set_text(code);
            };
            this.opened = false;
        };
    };


    FullEditWidget.prototype.toggle = function () {
        if (this.opened) {
            this.close();
        } else {
            this.open();
        };
    };


    IPython.FullEditWidget = FullEditWidget;

    return IPython;

}(IPython));
