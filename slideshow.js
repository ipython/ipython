Presentation Mode
=================
<div id='presentation_mode'>
    <style>
        .pmode{ display: none !important }
    </style>
    <script>
        pmode = function(){
        init()
        cells = $('.cell')
        $(cells).fadeOut();
        $(cells[0]).fadeIn()
        i = 0 
        nslide = function(){$(cells[i]).fadeOut(function(){i=i+1;$(cells[i]).fadeIn();});}
        pslide = function(){$(cells[i]).fadeOut(function(){i=i-1;$(cells[i]).fadeIn();});}
        $('#menubar, #pager_splitter, #pager, #header,#toolbar').addClass('pmode');
        //setInterval(nslide,1000)
        //
        };
        
        var init = function()
        {
            var pt = $('<div/>').attr('id','toolbar_present').addClass('toolbar');
            $('#toolbar').after(pt);
            ptoolbar = new IPython.ToolBar('#toolbar_present');
            IPython.ptoolbar = ptoolbar;
            ptoolbar.addButtonsGroup([{'label':'Next Slide', 'icon':'ui-icon-stop', 'callback':function(){stop()}}])
            ptoolbar.addButtonsGroup([
                                      {'label':'Next Slide', 'icon':'ui-icon-seek-prev', 'callback':function(){pslide()}},
                                      {'label':'Next Slide', 'icon':'ui-icon-seek-next', 'callback':function(){nslide()}},
                                      ])
        }
        
        var stop = function() {
            $(cells).show();
            $(ptoolbar.selector).remove();
            $('.pmode').removeClass('pmode');
        }
        
        var sid = '#start_pmode'
        if(($(sid)).length == 0) {
            IPython.toolbar.addButtonsGroup([
                                      {'label':'Start Slideshow', 'icon':'ui-icon-image', 'callback':function(){pmode()},'id':sid},
                                      ])
            }
        //pmode()

    </script>
</div>

