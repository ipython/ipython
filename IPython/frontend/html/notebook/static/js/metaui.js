//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MetaUI
//============================================================================

var IPython = (function (IPython) {
    "use strict";


    var MetaUI = function () {
        this.subelements = [];
        this.metainner = $('<div/>')
        var cell =  $('<div></div>').addClass('cell border-box-sizing code_cell vbox');
        var that = this;
        var metawrapper = $('<div/>').addClass('metaedit')
                .append(this.metainner)
                .hover(function(){that.fadeI()},function(){that.fadeO()})
    //
        this.add_button(['button -a-','button -b-','button -c-']);
        this.add_button(['button -1-','button -2-','button -3-']);
        this.add_button(['button ---','button +++','button ===']);

        return metawrapper;
    };
   

    MetaUI.prototype.fadeO = function(){
        //fadeout all inner element unless they are sticky
        var sb = this.subelements;
        for(var i in sb){
            if(sb[i].sticky != true){
                $(sb[i]).fadeOut("fast")
            }
        }
    }

    MetaUI.prototype.fadeI = function(){
        //FadeIn all elements
        for(var i in this.subelements){
            this.subelements[i].fadeIn("fast")
        }
    }



    MetaUI.prototype.add_button = function (labels) {
       var labels = labels || ["on","off"]
       var button =  $('<div/>').button({label:labels[0]})
           button.click(function(){
               button.value = (button.value+1)% labels.length || 0;
               $(button).button( "option", "label",labels[button.value]);
            });
       this.subelements.push(button);
       this.metainner.append(button)
       return button
    }


    IPython.MetaUI = MetaUI;

    return IPython;
}(IPython));
