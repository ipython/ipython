//----------------------------------------------------------------------------
//  Copyright (C) 2008-2012  The IPython Development Team
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

var IPython = (function (IPython) {
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
            var c0 = cpl[0];
            var c1 = cpl[cpl.length-1];
            
            common = longestCommonSubstring(c0, c1).sequence;

            if(common !== undefined ){
                cm.replaceRange(common, data.from, data.to);
            }
        };
    };
    
    var MultiHint = function(){
        this.complete_source = [];
        this._complete_callback = undefined;
        this._pending_requests = 0;
        this._pending_results = null;
        
        
    };
    
    MultiHint.prototype._gather_source = function(obj){
        
        this._pending_requests = this._pending_requests -1;

        if(!this._pending_results){
            this._pending_results = obj;
            
        } else {
            for(var idx in obj.list){
                this._pending_results.list = this._pending_results.list || [];
                this._pending_results.list.push(obj.list[idx]);
                
            }
             
            this._pending_results.from = this._pending_results.from || obj.from;
            this._pending_results.to = this._pending_results.to || obj.to;
        }
        
        if(this._pending_requests === 0){
            this._complete_callback(this._pending_results);
            this._pending_results = undefined;
        }
    };
    
    MultiHint.prototype.complete = function(cm, finish_complete_callback, options){
        
        this._complete_callback = finish_complete_callback;
        for(var i=0 ; i < this.complete_source.length; i++){
            this._pending_requests = this._pending_requests +1;
            this.complete_source[i](cm, $.proxy(this._gather_source,this), options);
        }
        return ;
    };
    
    
    IPython.cmutils = {
        MultiHint : MultiHint,
        insertLonguestCommonSubstring: insertLonguestCommonSubstring,
        recent_cm:recent_cm,
    
    };

    return IPython;
}(IPython));