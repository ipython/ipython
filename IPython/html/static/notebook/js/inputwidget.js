
var IPython = (function (IPython) {
    "use strict";


    var key   = IPython.utils.keycodes;

    var InputWidget = function () {
        this.output_msg_id = null;
        this.outstanding = 0;
        this.limit = 3;
    }

    InputWidget.prototype.execute = function (cell) {
        var that = this;
        if (this.outstanding >= this.limit) {
            return;
        }
        
        var handle_output = function (msg) {
            if (!that.output_msg_id) {
                that.output_msg_id = msg.parent_header.msg_id;
            }
            if (that.output_msg_id !== msg.parent_header.msg_id) {
                cell.clear_output(true);
                that.output_msg_id = msg.parent_header.msg_id
            }
            cell.output_area.handle_output(msg)
        }
        
        var callbacks = {
            shell : {
                reply : function () {that.outstanding--;}
            },
            iopub : {
                output : handle_output,
                clear_output : $.proxy(cell.output_area.handle_clear_output, cell.output_area),
            },
        };
        
        cell.kernel.execute(
            cell.get_text(), callbacks, {silent: false, store_history: false}
        );
        this.outstanding++;
    }

    InputWidget.prototype.replace = function (cell, new_text) {
        cell.code_mirror.replaceSelection(new_text);
    }


    InputWidget.prototype.handle = function (cell, text) {
        this.outstanding = 0;
        this.output_msg_id = null;
    }

    var IntWidget = function () {
        InputWidget.apply(this);
    }
    
    IntWidget.prototype = new InputWidget();

    IntWidget.prototype.handle = function (cell, text) {
        var that = this;
        // cell.clear_output();
        // that.execute(cell);
        InputWidget.prototype.handle.apply(this);
        var initial = parseInt(text);
        var min = -initial;
        var max = 3*initial;
        var range = $('<input/>').
            attr('type', 'range').attr('value', initial).
            attr('min', min).attr('max', max).
            attr('step', 1);
        range.on('change', function () {
            that.replace(cell, $(this).val());
            that.execute(cell);
        });
        var range_cont = $('<div/>').addClass('range-widget').
            append($('<i/>').addClass('icon-remove').click(function () {
                $(this).parent().remove();
                cell.code_mirror.focus();
            })).
            append(range);
        range_cont.on('focusout', function () {
            $(this).remove();
        })
        range_cont.on('keyup', function (event) {
            if (event.keyCode === key.ALT) {
                $(this).remove();
                cell.code_mirror.focus();
            }
        })
        cell.element.append(range_cont);
        cell.element.css('position', 'relative');
        var cc = cell.code_mirror.cursorCoords(true);
        var pos = cell.element.offset();
        var base_width = range.outerWidth() + 24;
        range_cont.width(base_width)
        var left = cc.left-pos.left-base_width/2;
        var top = cc.top-pos.top-32;
        range_cont.css('position', 'absolute').
            css('z-index', '2').
            css('left', left).
            css('top', top).
            css('padding', '3px').
            css('background-color', 'white').
            addClass('ui-widget-content').
            addClass('corner-all');
        range_cont.focusin();
    };

    var int_widget = new IntWidget();

    IPython.CodeCell.register_input_widget("^(-)?[0-9]+$", $.proxy(int_widget.handle, int_widget));
    IPython.int_widget = int_widget;

    return IPython;

}(IPython));