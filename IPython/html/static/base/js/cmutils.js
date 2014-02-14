//----------------------------------------------------------------------------
//  Copyright (C) 2014 - The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CodeMirror Utilities
//============================================================================
IPython.namespace('IPython.cmutils');


/* local util for codemirror */
var posEq = function (a, b) {
    "use strict";
    return a.line === b.line && a.ch === b.ch;
};

/**
 * function to delete until previous non blanking space character
 * or first multiple of 4 tabstop.
 * @private
 */
CodeMirror.commands.delSpaceToPrevTabStop = function(cm){
    "use strict";
    var from = cm.getCursor(true), to = cm.getCursor(false);
    if (!posEq(from, to)) { cm.replaceRange("", from, to); return; }
    var cur = cm.getCursor();
    var tabsize = cm.getOption('tabSize');
    var chToPrevTabStop = cur.ch-(Math.ceil(cur.ch/tabsize)-1)*tabsize;
    from = {ch:cur.ch-chToPrevTabStop,line:cur.line};
    var select = cm.getRange(from,cur);
    if( select.match(/^\ +$/) !== null){
        cm.replaceRange("",from,cur);
    } else {
        cm.deleteH(-1,"char");
    }
};

var IPython = (function (IPython, CodeMirror) {
    var utils = IPython.utils;
    
    var longestCommonSubstring = utils.longestCommonSubstring;
    
    /**
     * CodeMirror had some bug in =<3.21.1, that shoud be fixed now.
     * some option will not work in codemirror 3.21.1, but will work fine
     * in later versions. 
     * 
     * So this is mainly not to have to re-implement the logic
     * for IPython 2.x, to be use in dev-version and/or if pacakging of 
     * distributions ship codemirror 3.21.2 with IPython 2.0.
     * Once we bundle a codemirror version that does not present thoses bugs, 
     * all logics that use this function shoudl be removed.
     * 
     * TODO: remove once we update codemirror.
     **/
    var recent_cm = function(CodeMirror){
        return true;
        var cmv =  CodeMirror.version.split('.');    
        if(parseInt(cmv[0]) >= 4){
            return true;
        } else {
            if(parseInt(cmv[0]) == 3 && parseInt(cmv[1]) > 21) {
                return true;
            }
        }
        return false;
        
    };
    
    /**
     * Tab should not pick() the result
     * but insert the longuest common prefix. 
     * this is doable only on master CM
     * for now.
     **/
    var insertLonguestCommonSubstring = function(cm){
        return function(cp, obj){
            var data = obj.data;
            // CM not patched, fails gracefully by pick() highlight result.
            if(!recent_cm(CodeMirror)){
                console.log('need more recent version of CodeMirror to complete to common prefix.');
                return;
            }
            // if only one object, pick() it
            // as it is the only completion
            
            var cpl = obj.data.list;
            if(cpl.length === 1){
                obj.pick();
                return;
            }
            
            var common;
            var comp0 = cpl[0];
            var c0 = comp0.text;
            var c1 = cpl[cpl.length-1].text;
            
            common = longestCommonSubstring(c0, c1).sequence;

            if(common !== undefined ){
                cm.replaceRange(common, comp0.from, comp0.to);
            }
        };
    };
    
    /**
     * Proxy object to fetch completion from manysources at one.
     * push normal codemirror async sources  to `this.complete_source`.
     * and use `this.complete` as a new completion callback
     */
    var MultiHint = function(){
        this.complete_source = [];
        this._complete_callback = undefined;
        this._pending_requests = 0;
        this._pending_results = null;
    };
    
    /**
     * gather response from source, and trigger the real codemirror
     * callback once theyhave all responded.
     **/
    MultiHint.prototype._gather_source = function(obj){

        this._pending_requests = this._pending_requests -1;
        
        // Codemirror provide 2 kinds of completions form : 
        // {from;to;[str]}
        // or 
        // [{from,to,str}]
        // when merging we shoudl absolutly use the second
        // as source are inconsistent
        if(!this._pending_results){
            this._pending_results = {list:[]};
        } 
        
        // rely on underscore, usable in node, not jQuery
        var known_completions = _.map(this._pending_results.list,function(x){return x.text;});

        for(var idx in obj.list){
            //should deduplicate result from the different sources here
            var tmp ={};
            tmp.text = obj.list[idx];
            if(known_completions.indexOf(tmp.text)!== -1){
                continue;
            }
            tmp.from = obj.from;  
            tmp.to = obj.to;
            this._pending_results.list.push(tmp);
        }
        
        
        if(this._pending_requests === 0){
            this._complete_callback(this._pending_results);
            this._pending_results = undefined;
        }
    };
    
    // this shoudl probably be `$.proxy`'d or `_.bind`'ed  to work 
    // but we try to avoid reference to jquery or underscore here. 
    MultiHint.prototype.complete = function(cm, finish_complete_callback, options){
        
        this._complete_callback = finish_complete_callback;
        for(var i=0 ; i < this.complete_source.length; i++){
            this._pending_requests = this._pending_requests +1;
            this.complete_source[i](cm, _.bind(this._gather_source,this), options);
        }
        return ;
    };
    
    /**
     * This set up all the bindings option for the completions
     * once the completer is invoked
     * 
     * if pass is true completion will be triger
     * __and__ the key will be handled py codemirror. eg:
     * typing `np.` will show on `np.` not `np`.
     *
     * in the other hand, `tab` should trigger completion without
     * happending a tab char to the document.
     **/
    var completion_request = function(pass, complete_function){
        return function(cm) {
            setTimeout(function() {
              if (!cm.state.completionActive)
                CodeMirror.showHint(cm, complete_function, {
                    async: true,
                    // if characters is inserted do not autopick 
                    // or `foo.` automatically complete to `foo.foo`
                    completeSingle: !pass,
                    extraKeys: {
                        /**
                         * Tab should not pick() the result
                         * but insert the longuest common prefix. 
                         * this is doable only on master of CM
                         * for now.
                         **/
                        // need codemirror closure here for now.
                        // TODO though wether longuest common subsequece would make sens.
                        // and/or LCS of array of string.
                        "Tab" : insertLonguestCommonSubstring(cm)
                    }
                
                } );
            }, 100);
            // we may want to lower this timeout, but that's what is used in 
            // Codemirror examples.
            if(pass===true){
                return CodeMirror.Pass;
            } else {
                return;
            }

        }; 
    };
    
    IPython.cmutils = {
        insertLonguestCommonSubstring: insertLonguestCommonSubstring,
        completion_request: completion_request,
        MultiHint : MultiHint,
        recent_cm:recent_cm,
    };

    return IPython;
}(IPython, CodeMirror));