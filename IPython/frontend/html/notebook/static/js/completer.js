// function completer.
//
// completer should be a class that take an editor instance, and a list of
// function to call to get the list of completion.
//
// the function that send back the list of completion should received the
// editor handle as sole argument, and should return a json object with the
// following structure

// {list: clist,     # list of n string containing the completions
//  type : rp,       # list of n string containingtype/ origin of the completion 
//                   # (will be set as the class of the <option> to be able to style
//                   # them according to the origin of the completion)
//  from: {line: cur.line, ch: token.start}, 
//    to: {line: cur.line, ch: token.end}
//  };
//

var IPython = (function(IPython ) {
    // that will prevent us froom missspelling
    "use strict";

    // easyier key mapping
    var key = IPython.utils.keycodes;
    
    // what is the common start of all completions
    function sharedStart(B){
            if(B.length == 1){return B[0]}
            var A = new Array()
            for(var i=0; i< B.length; i++)
            {
               A.push(B[i].str); 
            }
            if(A.length > 1 ){
                var tem1, tem2, s, A = A.slice(0).sort();
                tem1 = A[0];
                s = tem1.length;
                tem2 = A.pop();
                while(s && tem2.indexOf(tem1) == -1){
                    tem1 = tem1.substring(0, --s);
                }
                if (tem1 == ""  || tem2.indexOf(tem1) != 0){return null;}
                return { str  : tem1,
                         type : "computed",
                         from : B[0].from,
                         to   : B[0].to
                };
            }
            return null;
        }

    // user to nsert the given completion
    var Completer = function(editor,getHints) {
        this.editor = editor;
        this.hintfunc = getHints;
        // if last caractere before cursor is not in this, we stop completing
        this.reg = /[A-Za-z.]/;
    }

    Completer.prototype.startCompletion = function()
    {
        // call for a 'first' completion, that will set the editor and do some 
        // special behaviour like autopicking if only one completion availlable
        //
        if (this.editor.somethingSelected()) return;
        this.done = false;
        // use to get focus back on opera
        this.carryOnCompletion(true);
    }

    Completer.prototype.carryOnCompletion = function(ff)
    {
        // pass true as parameter if you want the commpleter to autopick 
        // when only one completion
        // as this function is auto;atically reinvoked at each keystroke with 
        // ff = false
        var cur = this.editor.getCursor();
        var pre_cursor = this.editor.getRange({line:cur.line,ch:cur.ch-1},cur);

        // we nned to check that we are still on a word boundary
        // because while typing the completer is still reinvoking itself
        if(!this.reg.test(pre_cursor)){ this.close(); return;}
       
        this.autopick = false;
        if( ff != 'undefined' && ff==true)
        {
            this.autopick=true;
        }
        // We want a single cursor position.
        if (this.editor.somethingSelected()) return;

        // there we will need to gather the results for all the function (and merge them ?)
        // lets assume for now only one source
        //
        var that = this;
        this.hintfunc(function(result){that._resume_completion(result)});
    }
    Completer.prototype._resume_completion = function(results)
    {
        this.raw_result = results;

        // if empty result return
        if (!this.raw_result || !this.raw_result.length) return;



        // When there is only one completion, use it directly.
        if (this.autopick == true && this.raw_result.length == 1)
            {
                this.insert(this.raw_result[0]);
                return true;
            }

        if (this.raw_result.length == 1)
        {
        // test if first and only completion totally matches 
        // what is typed, in this case dismiss
        var str = this.raw_result[0].str
        var cur = this.editor.getCursor();
        var pre_cursor = this.editor.getRange({line:cur.line,ch:cur.ch-str.length},cur);
        if(pre_cursor == str){
            this.close();
            return ;
            }
        }

        this.complete = $('<div/>').addClass('completions');
        this.complete.attr('id','complete');

        this.sel = $('<select/>')
                .attr('multiple','true')
                .attr('size',Math.min(10,this.raw_result.length));
        var pos = this.editor.cursorCoords();

        // TODO: I propose to remove enough horizontal pixel
        // to align the text later
        this.complete.css('left',pos.x+'px');
        this.complete.css('top',pos.yBot+'px');
        this.complete.append(this.sel);

        $('body').append(this.complete);
        //build the container
        var that = this;
        this.sel.dblclick(function(){that.pick()});
        this.sel.blur(this.close);
        this.sel.keydown(function(event){that.keydown(event)});

        this.build_gui_list(this.raw_result);
        var that=this; 
        //CodeMirror.connect(that.sel, "dblclick", function(){that.pick()});

        this.sel.focus();
        // Opera sometimes ignores focusing a freshly created node
        if (window.opera) setTimeout(function(){if (!this.done) this.sel.focus();}, 100);
        // why do we return true ?
        return true;
    }

    Completer.prototype.insert = function(completion) {
        this.editor.replaceRange(completion.str, completion.from, completion.to);
        }

    Completer.prototype.build_gui_list = function(completions){
        // Need to clear the all list
        for (var i = 0; i < completions.length; ++i) {
            var opt = $('<option/>')
                .text(completions[i].str)
                .addClass(completions[i].type);
            this.sel.append(opt);
        }
        this.sel.children().first().attr('selected','true');
        
        //sel.size = Math.min(10, completions.length);
        // Hack to hide the scrollbar.
        //if (completions.length <= 10)
        //this.complete.style.width = (this.sel.clientWidth - 1) + "px";
    }

    Completer.prototype.close = function() {
            if (this.done) return;
            this.done = true;
            $('.completions').remove();
        }

    Completer.prototype.pick = function(){
        this.insert(this.raw_result[this.sel[0].selectedIndex]);
        this.close();
        var that = this;
        setTimeout(function(){that.editor.focus();}, 50);
        }

                
    Completer.prototype.keydown = function(event) {
      var code = event.keyCode;
      // Enter
      if (code == key.enter) {CodeMirror.e_stop(event); this.pick();}
      // Escape or backspace
      else if (code == key.esc ) {CodeMirror.e_stop(event); this.close(); this.editor.focus();}
      else if (code == key.space || code == key.backspace) {this.close(); this.editor.focus();}
      else if (code == key.tab){
            //all the fastforwarding operation, 
            //Check that shared start is not null which can append with prefixed completion
            // like %pylab , pylab have no shred start, and ff will result in py<tab><tab>
            // to erase py
            var sh = sharedStart(this.raw_result);
            if(sh){
                this.insert(sh);
            }
            this.close(); 
            CodeMirror.e_stop(event);
            this.editor.focus();
            //reinvoke self
            var that = this;
            setTimeout(function(){that.carryOnCompletion();}, 50);
      }
      else if (code == key.upArrow || code == key.downArrow) {
        // need to do that to be able to move the arrow 
        // when on the first or last line ofo a code cell
        event.stopPropagation();
      }
      else if (code != key.upArrow && code != key.downArrow) {
        this.close(); this.editor.focus();
        //we give focus to the editor immediately and call sell in 50 ms
        var that = this;
        setTimeout(function(){that.carryOnCompletion();}, 50);
      }
    }


    IPython.Completer = Completer;

    return IPython;
}(IPython));
