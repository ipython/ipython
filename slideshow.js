<div id='presentation_mode'>
    <link rel="stylesheet" href="../static/css/printnotebook.css" type="text/css">
    <style>
        #menubar{ display: none !important }
        #pager{ display: none !important }
        #pager_splitter{ display: none !important }
    </style>

    <script>
        pmode = function(){
        console.log('executed script');
        cells = $('.cell')
        //$(cells).fadeOut();
        $(cells[0]).fadeIn()
        var i = 0 
        nslide = function(){$(cells[i]).fadeOut(function(){i=i+1;$(cells[i]).fadeIn();});}
        //setInterval(nslide,1000)
        //
        var pt = $('<div/>').attr('id','toolbar_present')
            pt.addClass('border-box-sizing ui-widget ui-widget-content');
            pt.attr('style','border-top-style: none; border-left-style: none; border-right-style: none; ');
        $('#toolbar').after(pt);
        };
        
        pmode()

    </script>
</div>
