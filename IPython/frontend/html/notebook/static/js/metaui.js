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


    var MetaUI = function (cell) {
        this.subelements = [];
        this.metainner = $('<div/>');
        this.cell = cell;
        var that = this;
        var metawrapper = $('<div/>').addClass('metaedit')
                .append(this.metainner)
                .hover(function(){that.fadeI()},function(){that.fadeO()})
        this.fadeI();
        this.add_button('bt1',['Group Stop','Slide Stop','Show With Previous',"Never Show"]);
        this.add_button('bt2',['In & Out','In / Out','In Only','Out Only']);
        //this.add_button('bt3',['button ---','button +++','button ===']);
        this.fadeO();
        return metawrapper;
    };
   

    MetaUI.prototype.fadeO = function(){
        //fadeout all inner element unless they are sticky
        this.cell.metadata.test = 1;
        var sb = this.subelements;
        for(var i in sb){
            if(sb[i].sticky != true){
                $(sb[i]).fadeTo("fast",0)
            }
        }
    }

    MetaUI.prototype.fadeI = function(){
        //FadeIn all elements
        for(var i in this.subelements){
            this.subelements[i].fadeTo("fast",1)
        }
    }



    MetaUI.prototype.add_button = function (sk,labels) {
       var labels = labels || ["on","off"]
       var that = this;
       var button =  $('<div/>').button({label:labels[0]})
           button.value = 0;
           button.click(function(){
               button.value = (button.value+1)% labels.length || 0;
               button.sticky = (button.value != 0);
               that.cell.metadata[sk] = labels[button.value];
               $(button).button( "option", "label",labels[button.value]);
            });
       this.subelements.push(button);
       this.metainner.append(button)
       return button
    }


    IPython.MetaUI = MetaUI;

    return IPython;
}(IPython));
