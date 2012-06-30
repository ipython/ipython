// function completer.
//
// completer should be a class that take an cell instance
var IPython = (function (IPython) {
    // that will prevent us from misspelling
    "use strict";

    // easyier key mapping
    var key = IPython.utils.keycodes;

    function prepend_n_prc(str, n) {
        for( var i =0 ; i< n ; i++)
        { str = '%'+str }
        return str;
    }

    function _existing_completion(item, completion_array){
       for( var c in completion_array ) {
           if(completion_array[c].substr(-item.length) == item)
           { return true; }
       }
       return false;
    }

    // what is the common start of all completions
    function shared_start(B, drop_prct) {
        if (B.length == 1) {
            return B[0];
        }
        var A = new Array();
        var common;
        var min_lead_prct = 10;
        for (var i = 0; i < B.length; i++) {
            var str = B[i].str;
            var localmin = 0;
            if(drop_prct == true){
                while ( str.substr(0, 1) == '%') {
                    localmin = localmin+1;
                    str = str.substring(1);
                }
            }
            min_lead_prct = Math.min(min_lead_prct, localmin);
            A.push(str);
        }

        if (A.length > 1) {
            var tem1, tem2, s;
            A = A.slice(0).sort();
            tem1 = A[0];
            s = tem1.length;
            tem2 = A.pop();
            while (s && tem2.indexOf(tem1) == -1) {
                tem1 = tem1.substring(0, --s);
            }
            if (tem1 == "" || tem2.indexOf(tem1) != 0) {
                return prepend_n_prc('', min_lead_prct);
            }
            return {
                str: prepend_n_prc(tem1, min_lead_prct),
                type: "computed",
                from: B[0].from,
                to: B[0].to
            };
        }
        return null;
    }


    var Completer = function (cell) {
            this.editor = cell.code_mirror;
            var that = this;
            $([IPython.events]).on('status_busy.Kernel', function () {
                that.skip_kernel_completion = true;
            });
            $([IPython.events]).on('status_idle.Kernel', function () {
                that.skip_kernel_completion = false;
            });


        };



    Completer.prototype.startCompletion = function () {
        // call for a 'first' completion, that will set the editor and do some
        // special behaviour like autopicking if only one completion availlable
        //
        if (this.editor.somethingSelected()) return;
        this.done = false;
        // use to get focus back on opera
        this.carry_on_completion(true);
    };

    Completer.prototype.carry_on_completion = function (ff) {
        // Pass true as parameter if you want the commpleter to autopick when
        // only one completion. This function is automatically reinvoked at
        // each keystroke with ff = false
        var cur = this.editor.getCursor();
        var line = this.editor.getLine(cur.line);
        var pre_cursor = this.editor.getRange({
            line: cur.line,
            ch: cur.ch - 1
        }, cur);

        // we need to check that we are still on a word boundary
        // because while typing the completer is still reinvoking itself
        if (!/[0-9a-z._/\\:~-]/i.test(pre_cursor)) {
            this.close();
            return;
        }

        this.autopick = false;
        if (ff != 'undefined' && ff == true) {
            this.autopick = true;
        }

        // We want a single cursor position.
        if (this.editor.somethingSelected()) return;

        // one kernel completion came back, finish_completing will be called with the results
        // we fork here and directly call finish completing if kernel is busy
        if (this.skip_kernel_completion == true) {
            this.finish_completing({
                'matches': [],
                matched_text: ""
            })
        } else {
            var callbacks = {
                'complete_reply': $.proxy(this.finish_completing, this)
            };
            IPython.notebook.kernel.complete(line, cur.ch, callbacks);
        }
    };

    Completer.prototype.finish_completing = function (content) {
        // let's build a function that wrap all that stuff into what is needed
        // for the new completer:
        var matched_text = content.matched_text;
        var matches = content.matches;

        var cur = this.editor.getCursor();
        var results = CodeMirror.contextHint(this.editor);
        var filterd_results = Array();
        //remove results from context completion
        //that are already in kernel completion
        for(var elm in results) {
            if(_existing_completion(results[elm]['str'], matches) == false)
            { filterd_results.push(results[elm]); }
        }

        // append the introspection result, in order, at at the beginning of
        // the table and compute the replacement range from current cursor
        // positon and matched_text length.
        for (var i = matches.length - 1; i >= 0; --i) {
            filterd_results.unshift({
                str: matches[i],
                type: "introspection",
                from: {
                    line: cur.line,
                    ch: cur.ch - matched_text.length
                },
                to: {
                    line: cur.line,
                    ch: cur.ch
                }
            });
        }

        // one the 2 sources results have been merge, deal with it
        this.raw_result = filterd_results;

        // if empty result return
        if (!this.raw_result || !this.raw_result.length) return;

        // When there is only one completion, use it directly.
        if (this.autopick == true && this.raw_result.length == 1) {
            this.insert(this.raw_result[0]);
            return;
        }

        if (this.raw_result.length == 1) {
            // test if first and only completion totally matches
            // what is typed, in this case dismiss
            var str = this.raw_result[0].str;
            var pre_cursor = this.editor.getRange({
                line: cur.line,
                ch: cur.ch - str.length
            }, cur);
            if (pre_cursor == str) {
                this.close();
                return;
            }
        }

        this.complete = $('<div/>').addClass('completions');
        this.complete.attr('id', 'complete');

        this.sel = $('<select/>').attr('multiple', 'true').attr('size', Math.min(10, this.raw_result.length));
        var pos = this.editor.cursorCoords();

        // TODO: I propose to remove enough horizontal pixel
        // to align the text later
        this.complete.css('left', pos.x + 'px');
        this.complete.css('top', pos.yBot + 'px');
        this.complete.append(this.sel);

        $('body').append(this.complete);
        //build the container
        var that = this;
        this.sel.dblclick(function () {
            that.pick();
        });
        this.sel.blur(this.close);
        this.sel.keydown(function (event) {
            that.keydown(event);
        });

        this.build_gui_list(this.raw_result);

        this.sel.focus();
        // Opera sometimes ignores focusing a freshly created node
        if (window.opera) setTimeout(function () {
            if (!this.done) this.sel.focus();
        }, 100);
        return true;
    }

    Completer.prototype.insert = function (completion) {
        this.editor.replaceRange(completion.str, completion.from, completion.to);
    }

    Completer.prototype.build_gui_list = function (completions) {
        // Need to clear the all list
        for (var i = 0; i < completions.length; ++i) {
            var opt = $('<option/>').text(completions[i].str).addClass(completions[i].type);
            this.sel.append(opt);
        }
        this.sel.children().first().attr('selected', 'true');
    }

    Completer.prototype.close = function () {
        if (this.done) return;
        this.done = true;
        $('.completions').remove();
    }

    Completer.prototype.pick = function () {
        this.insert(this.raw_result[this.sel[0].selectedIndex]);
        this.close();
        var that = this;
        setTimeout(function () {
            that.editor.focus();
        }, 50);
    }


    Completer.prototype.keydown = function (event) {
        var code = event.keyCode;
        var that = this;
        // Enter
        if (code == key.ENTER) {
            CodeMirror.e_stop(event);
            this.pick();
        }
        // Escape or backspace
        else if (code == key.ESC) {
            CodeMirror.e_stop(event);
            this.close();
            this.editor.focus();
        } else if (code == key.SPACE || code == key.BACKSPACE) {
            this.close();
            this.editor.focus();
        } else if (code == key.TAB) {
            //all the fastforwarding operation,
            //Check that shared start is not null which can append with prefixed completion
            // like %pylab , pylab have no shred start, and ff will result in py<tab><tab>
            // to erase py
            var sh = shared_start(this.raw_result, true);
            if (sh) {
                this.insert(sh);
            }
            this.close();
            CodeMirror.e_stop(event);
            this.editor.focus();
            //reinvoke self
            setTimeout(function () {
                that.carry_on_completion();
            }, 50);
        } else if (code == key.UPARROW || code == key.DOWNARROW) {
            // need to do that to be able to move the arrow
            // when on the first or last line ofo a code cell
            event.stopPropagation();
        } else if (code != key.UPARROW && code != key.DOWNARROW) {
            this.close();
            this.editor.focus();
            //we give focus to the editor immediately and call sell in 50 ms
            setTimeout(function () {
                that.carry_on_completion();
            }, 50);
        }
    }


    IPython.Completer = Completer;

    return IPython;
}(IPython));
