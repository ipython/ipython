//----------------------------------------------------------------------------
//  Copyright (C) 2008-2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// EngineInteract
//============================================================================

var key   = IPython.utils.keycodes;


var DirectViewWidget = function (selector, kernel, targets) {
    // The kernel doesn't have to be set at creation time, in that case
    // it will be null and set_kernel has to be called later.
    this.selector = selector;
    this.element = $(selector);
    this.kernel = kernel || null;
    this.code_mirror = null;
    this.targets = targets;
    this.create_element();
};


DirectViewWidget.prototype.create_element = function () {
    this.element.addClass('cell border-box-sizing code_cell vbox');
    this.element.attr('tabindex','2');
    this.element.css('padding-right',0);

    var control = $('<div/>').addClass('dv_control').height('30px');
    var control_label = $('<span/>').html('Select engine(s) to run code on interactively: ');
    control_label.css('line-height','30px');
    var select = $('<select/>').addClass('dv_select ui-widget ui-widget-content');
    select.css('font-size','85%%').css('margin-bottom','5px');
    var n = this.targets.length;
    select.append($('<option/>').html('all').attr('value','all'));
    for (var i=0; i<n; i++) {
        select.append($('<option/>').html(this.targets[i]).attr('value',this.targets[i]))
    }
    control.append(control_label).append(select);

    var input = $('<div></div>').addClass('input hbox');
    var input_area = $('<div/>').addClass('input_area box-flex1');
    this.code_mirror = CodeMirror(input_area.get(0), {
        indentUnit : 4,
        mode: 'python',
        theme: 'ipython',
        onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
    });
    input.append(input_area);
    var output = $('<div></div>');


    this.element.append(control).append(input).append(output);
	this.output_area = new IPython.OutputArea(output, false);

};


DirectViewWidget.prototype.handle_codemirror_keyevent = function (editor, event) {
    // This method gets called in CodeMirror's onKeyDown/onKeyPress
    // handlers and is used to provide custom key handling. Its return
    // value is used to determine if CodeMirror should ignore the event:
    // true = ignore, false = don't ignore.
  
    var that = this;
    var cur = editor.getCursor();

    if (event.keyCode === key.ENTER && event.shiftKey && event.type === 'keydown') {
        // Always ignore shift-enter in CodeMirror as we handle it.
        event.stop();
        that.execute();
        return true;
    } else if (event.keyCode === key.UP && event.type === 'keydown') {
        event.stop();
        return false;
    } else if (event.keyCode === key.DOWN && event.type === 'keydown') {
        event.stop();
        return false;
    } else if (event.keyCode === key.BACKSPACE && event.type == 'keydown') {
        // If backspace and the line ends with 4 spaces, remove them.
        var line = editor.getLine(cur.line);
        var ending = line.slice(-4);
        if (ending === '    ') {
            editor.replaceRange('',
                {line: cur.line, ch: cur.ch-4},
                {line: cur.line, ch: cur.ch}
            );
            event.stop();
            return true;
        } else {
            return false;
        };
    };

    return false;
};


// Kernel related calls.


DirectViewWidget.prototype.set_kernel = function (kernel) {
    this.kernel = kernel;
}


DirectViewWidget.prototype.execute = function () {
    this.output_area.clear_output(true, true, true);
    this.element.addClass("running");
    var callbacks = {
        'execute_reply': $.proxy(this._handle_execute_reply, this),
        'output': $.proxy(this.output_area.handle_output, this.output_area),
        'clear_output': $.proxy(this.output_area.handle_clear_output, this.output_area),
    };
    var target = this.element.find('.dv_select option:selected').attr('value');
    if (target === 'all') {
        target = '"all"';
    }
    var code = '%(widget_var)s.execute("""'+this.get_text()+'""",targets='+target+')';
    var msg_id = this.kernel.execute(code, callbacks, {silent: false});
    this.clear_input();
    this.code_mirror.focus();
};


DirectViewWidget.prototype._handle_execute_reply = function (content) {
    this.element.removeClass("running");
    // this.dirty = true;
}

// Basic cell manipulation.


DirectViewWidget.prototype.select_all = function () {
    var start = {line: 0, ch: 0};
    var nlines = this.code_mirror.lineCount();
    var last_line = this.code_mirror.getLine(nlines-1);
    var end = {line: nlines-1, ch: last_line.length};
    this.code_mirror.setSelection(start, end);
};


DirectViewWidget.prototype.clear_input = function () {
    this.code_mirror.setValue('');
};


DirectViewWidget.prototype.get_text = function () {
    return this.code_mirror.getValue();
};


DirectViewWidget.prototype.set_text = function (code) {
    return this.code_mirror.setValue(code);
};

container.show();
var widget = $('<div/>')
// When templating over a JSON string, we must use single quotes.
var targets = '%(targets)s';
targets = $.parseJSON(targets);
var eiw = new DirectViewWidget(widget, IPython.notebook.kernel, targets);
element.append(widget);
element.css('padding',0);
setTimeout(function () {
    eiw.code_mirror.refresh();
    eiw.code_mirror.focus();
}, 1);

