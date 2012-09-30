# -*- coding: utf-8 -*-
"""
%slidemode magic for notebook
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.display import HTML, Javascript, display_javascript
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.testing.skipdoctest import skip_doctest
#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------
### big  JS file
jscode0 = r"""
var bind_remote = function(selector){
    var cc = $('<input/>')
        .attr('id','azerty')
        .fadeTo(0.2,0)
        .keydown(
        function(event){
                if(event.which == IPython.utils.keycodes.LEFT_ARROW){
                    console.log('go left');
                    IPython.slideshow.prev();
                }
                else if(event.which == IPython.utils.keycodes.RIGHT_ARROW){
                    console.log('go right')
                    IPython.slideshow.next();   
                }
            event.preventDefault();
            return false;
            })
            .focusin(function(){$('#qwerty').button('option','label','Slide Mode Enabled')})
            .focusout(function(){$('#qwerty').button('option','label','Enable Slide Mode')})
        
        var dd = $('<div/>')
            .attr('id','qwerty')
            .button({label:'slide control'})
            .attr('style','float:right')
            .click(
                function(){
                    $('#azerty').focus();
                    console.log('...');
                })
            .keydown(
                function(event){
                    console.log('event append',event);
                event.preventDefault();
                return false;
                })
    var hin = function(){$(selector).fadeTo('slow',1);}
    var hout= function(){$(selector).fadeTo('slow',0.3);}        
    $(selector)
        .append(cc)
        .append(dd)
        .fadeTo('slow',0.3)
    .hover(hin,hout)
     
}
    
var show_line = function(cell,line_number){
    cell.code_mirror.showLine(cell.code_mirror.getLineHandle(line_number-1))    }
"""

jscode = r"""
    IPython = (function(IPython) {
    
    var Presentation = function(){
          this.ccell = 0;
      }

      var is_marked_cell = function(cell){
          return (cell.code_mirror.getValue().match(/(\n)?(<!--|#)?====(-->)?(\n)?/) != null)
      }
      Presentation.prototype.create_toolbar = function(){
            var pt = $('<div/>').attr('id','toolbar_present').addClass('toolbar');
            var that = this;
            this.avc = $('<div/>').button({label:that.eta()});
            pt.append(this.avc);

            $('#toolbar').after(pt);
            var ptoolbar = new IPython.ToolBar('#toolbar_present');
            IPython.ptoolbar = ptoolbar;
            ptoolbar.addButtonsGroup([{label:'Stop', icon:'ui-icon-stop', callback:function(){that.stop()}}])
            ptoolbar.addButtonsGroup([
                     {label:'Prev Slide', icon:'ui-icon-seek-prev', callback:function(){that.prev_group()}},
                     {label:'Next Slide', icon:'ui-icon-seek-next', callback:function(){that.next_group()}},
                                    ])
            ptoolbar.addButtonsGroup([
                     {label:'Step Next', icon:'ui-icon-play', callback:function(){that.next()}}
                     ])
            bind_remote('#toolbar_present');

      }

      Presentation.prototype.remove_toolbar = function(){
          $('#toolbar_present').remove();
      }

      Presentation.prototype.ngroups = function(){
          var cells = IPython.notebook.get_cells();
          var cnt =0
          for( var i=0; i< cells.length;i++)
              if(is_marked_cell(cells[i])) cnt++;
          return cnt
      }

      Presentation.prototype.cgroups = function(){
          var cells = IPython.notebook.get_cells();
          var cnt =0
          for( var i=0; i<= this.ccell ;i++)
              if(is_marked_cell(cells[i])) cnt++;
          return cnt
      }

      Presentation.prototype.eta = function(){
          return this.cgroups()+'/'+this.ngroups()
          }

      Presentation.prototype.next_marked_cell_n = function()
      {
          for(var i=this.ccell+1; i< $('.cell').length; i++)
          {
              if(is_marked_cell(IPython.notebook.get_cell(i)))
                { return i; }
          }
          return null;
      }

      Presentation.prototype.prev_marked_cell_n = function()
      {
          for(var i=this.ccell-1; i> 0; i--)
          {
              if(is_marked_cell(IPython.notebook.get_cell(i))){
                 return i
              }
          }
          return 0;
      }

      Presentation.prototype.start = function(){
          this.restart();
          this.resume();
      }

      Presentation.prototype.restart = function(){
          this.ccell = 0;
          delete this.avc;
      }

      Presentation.prototype.resume = function(){
          this.create_toolbar();
          $('#menubar, #pager_splitter, #pager, #header,#toolbar').addClass('pmode');
          $('.cell').fadeOut();
          if(this.current_is_marked()){
              $('.cell:nth('+this.ccell+')').fadeIn();
          } else {
              for( var i=this.prev_marked_cell_n() ; i<= this.ccell; i++){
                  $('.cell:nth('+i+')').fadeIn();
              }
          }
          var that=this;
          if(this.avc != undefined)
            $(this.avc).button('option','label',that.eta())
          return this;
      }

      Presentation.prototype.stop = function(){
          $('.cell').fadeIn();
          $('.pmode').removeClass('pmode');
          $('div#notebook').removeClass('pove');
          this.remove_toolbar();
      }

      Presentation.prototype.next = function(){
          this.ccell = this.ccell+1;
          var that = this;
          if(this.ccell >= $('.cell').length ){
              this.restart();
              this.stop();
              return;
          }
          var nnext = this.ccell;
          var ncell = IPython.notebook.get_cell(nnext)

          if(is_marked_cell(ncell)){
              $('.cell').fadeOut(500);
              setTimeout(function(){$('.cell:nth('+nnext+')').fadeIn(500)},600);
          } else {
              setTimeout(function(){$('.cell:nth('+nnext+')').fadeIn(500)},0);
          }
          $(this.avc).button('option','label',that.eta())
          return this;
      }

      Presentation.prototype.next_group = function(){
          this.ccell = this.next_marked_cell_n();
          var that = this;
          $('.cell').fadeOut(500);
          setTimeout(function(){
              $('.cell:nth('+that.ccell+')').fadeIn(500)
                  },600);
          $(this.avc).button('option','label',that.eta())
      }

      Presentation.prototype.prev_group = function(){
          this.ccell = this.prev_marked_cell_n();
          var that = this
          $('.cell').fadeOut(500);
          setTimeout(function(){$('.cell:nth('+that.ccell+')').fadeIn(500)},600);
          $(this.avc).button('option','label',that.eta())
      }

      Presentation.prototype.is_n_marked = function(n){
          return is_marked_cell(IPython.notebook.get_cell(n))
      }

      Presentation.prototype.current_is_marked = function(n){
          return is_marked_cell(IPython.notebook.get_cell(this.ccell));
      }

      Presentation.prototype.prev = function(){
          if(is_marked_cell(IPython.notebook.get_cell(this.ccell))){
              var pmcell = this.prev_marked_cell_n();
              $('.cell').fadeOut(500);
              for( var i=pmcell; i< this.ccell ; i++ ){
                  (function(val){
                      return function(){
                                  setTimeout( function(){
                                      $('.cell:nth('+val+')').fadeIn(500)
                                      },600);
                      }
                   })(i)();
              }
          } else {
              $('.cell:nth('+this.ccell+')').fadeOut(500);
          }
          this.ccell = this.ccell -1;
          return this;
      }

      IPython.Presentation = Presentation;
      return IPython;

    })(IPython);

    $('body').append($('<style/>').text('.pmode{ display: none !important }'));
    IPython.slideshow = new IPython.Presentation();

    var sid = 'start_pmode'
    if(($('#'+sid)).length == 0) {
          IPython.toolbar.addButtonsGroup([
                  {'label'  :'Start Slideshow',
                    'icon'  :'ui-icon-image',
                    'callback':function(){IPython.slideshow.resume()},'id':sid},
              ])
         }
"""



##
@magics_class
class StoreMagics(Magics):

    @skip_doctest
    @line_magic
    def slideshow_mode(self, parameter_s=''):
        display_javascript(Javascript(jscode0+jscode))


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(StoreMagics)
        _loaded = True
