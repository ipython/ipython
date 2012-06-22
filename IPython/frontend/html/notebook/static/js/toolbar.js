//----------------------------------------------------------------------------
//  Copyright (C) 2008 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// ToolBar
//============================================================================

var IPython = (function (IPython) {

    var ToolBar = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.construct();
            this.addDropDownList();
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    // add a group of button into the current toolbar.
    //
    // First argument : Mandatory
    //      list of dict as argument, each dict should contain
    //      3 mandatory keys and values :
    //      'label' : string -- the text to show on hover
    //      'icon'  : string -- the jQuery-ui icon to add on this button
    //      'callback' : function -- the callback to execute on a click
    //
    //      and optionnaly an 'id' key that is assigned to the button element
    //
    // Second Argument, optionnal,
    //      string reprensenting the id to give to the button group.
    //
    // Example
    //
    // IPython.toolbar.addButtonsGroup([
    //  {'label':'my button',
    //   'icon':'ui-icon-disk',
    //   'callback':function(){alert('hoho'),
    //   'id' : 'my_button_id',                 // this is optionnal
    //   }
    //  },
    //  {'label':'my second button',
    //   'icon':'ui-icon-scissors',
    //   'callback':function(){alert('be carefull I cut')}
    //  }
    //  ],
    //  "my_button_group_id"
    //  )
    //
    ToolBar.prototype.addButtonsGroup = function(list, group_id){
        var span_group = $('<span/>');
        if( group_id != undefined )
            span_group.attr('id',group_id)
        for(var el in list)
        {
            var button  = $('<button/>').button({
                icons : {primary: list[el]['icon']},
                text : false,
                label: list[el]['label'],
                });
            var id = list[el]['id'];
            if( id != undefined )
                button.attr('id',id);
            var fun = list[el]['callback']
            button.click(fun);
            span_group.append(button);
        }
        span_group.buttonset();
        $(this.selector).append(span_group)
    }

    ToolBar.prototype.style = function () {
        this.element.addClass('border-box-sizing').
            addClass('ui-widget ui-widget-content toolbar').
            css('border-top-style','none').
            css('border-left-style','none').
            css('border-right-style','none');
    };

    ToolBar.prototype.addDropDownList = function()
    {
        var select = $(this.selector)
            .append($('<select/>')
                .attr('id','cell_type')
                .addClass('ui-widget ui-widget-content')
                    .append($('<option/>').attr('value','code').text('Code'))
                    .append($('<option/>').attr('value','markdown').text('Markdown'))
                    .append($('<option/>').attr('value','raw').text('Raw Text'))
                    .append($('<option/>').attr('value','heading1').text('Heading 1'))
                    .append($('<option/>').attr('value','heading2').text('Heading 2'))
                    .append($('<option/>').attr('value','heading3').text('Heading 3'))
                    .append($('<option/>').attr('value','heading4').text('Heading 4'))
                    .append($('<option/>').attr('value','heading5').text('Heading 5'))
                    .append($('<option/>').attr('value','heading6').text('Heading 6'))
                    .append($('<option/>').attr('value','heading7').text('Heading 7'))
                    .append($('<option/>').attr('value','heading8').text('Heading 8'))
                );
    }

    ToolBar.prototype.construct = function() {
        this.addButtonsGroup([
                {
                    'id':'save_b',
                    'label':'Save',
                    'icon':'ui-icon-disk',
                    'callback':function(){
                        IPython.notebook.save_notebook();
                        },
                },
            ]);
        this.addButtonsGroup([
                {
                    'id':'cut_b',
                    'label':'Cut Cell',
                    'icon':'ui-icon-scissors',
                    'callback':function(){
                        IPython.notebook.cut_cell();
                        },
                },
                {
                    'id':'copy_b',
                    'label':'Copy Cell',
                    'icon':'ui-icon-copy',
                    'callback':function(){
                        IPython.notebook.copy_cell();
                        },
                },
                {
                    'id':'paste_b',
                    'label':'Paste Cell',
                    'icon':'ui-icon-clipboard',
                    'callback':function(){
                        IPython.notebook.paste_cell();
                        },
                },
            ],'cut_copy_paste');

        this.addButtonsGroup([
                {
                    'id':'move_up_b',
                    'label':'Move Cell Up',
                    'icon':'ui-icon-arrowthick-1-n',
                    'callback':function(){
                        IPython.notebook.move_cell_up();
                        },
                },
                {
                    'id':'move_down_b',
                    'label':'Move Cell Down',
                    'icon':'ui-icon-arrowthick-1-s',
                    'callback':function(){
                        IPython.notebook.move_cell_down();
                        },
                },
            ],'move_up_down');
        
        this.addButtonsGroup([
                {
                    'id':'insert_above_b',
                    'label':'Insert Cell Above',
                    'icon':'ui-icon-arrowthickstop-1-n',
                    'callback':function(){
                        IPython.notebook.insert_cell_above('code');
                        },
                },
                {
                    'id':'insert_below_b',
                    'label':'Insert Cell Below',
                    'icon':'ui-icon-arrowthickstop-1-s',
                    'callback':function(){
                        IPython.notebook.insert_cell_below('code');
                        },
                },
            ],'insert_above_below');

        this.addButtonsGroup([
                {
                    'id':'run_b',
                    'label':'Run Cell',
                    'icon':'ui-icon-play',
                    'callback':function(){
                    IPython.notebook.execute_selected_cell();
                        },
                },
                {
                    'id':'interrupt_b',
                    'label':'Interrupt',
                    'icon':'ui-icon-stop',
                    'callback':function(){
                        IPython.notebook.kernel.interrupt();
                        },
                },
            ],'run_int');


    }
    ToolBar.prototype.bind_events = function () {
        var that = this;
        
        this.element.find('#cell_type').change(function () {
            var cell_type = $(this).val();
            if (cell_type === 'code') {
                IPython.notebook.to_code();
            } else if (cell_type === 'markdown')  {
                IPython.notebook.to_markdown();
            } else if (cell_type === 'raw')  {
                IPython.notebook.to_raw();
            } else if (cell_type === 'heading1')  {
                IPython.notebook.to_heading(undefined, 1);
            } else if (cell_type === 'heading2')  {
                IPython.notebook.to_heading(undefined, 2);
            } else if (cell_type === 'heading3')  {
                IPython.notebook.to_heading(undefined, 3);
            } else if (cell_type === 'heading4')  {
                IPython.notebook.to_heading(undefined, 4);
            } else if (cell_type === 'heading5')  {
                IPython.notebook.to_heading(undefined, 5);
            } else if (cell_type === 'heading6')  {
                IPython.notebook.to_heading(undefined, 6);
            };
        });
        $([IPython.events]).on('selected_cell_type_changed.Notebook', function (event, data) {
            if (data.cell_type === 'heading') {
                that.element.find('#cell_type').val(data.cell_type+data.level);
            } else {
                that.element.find('#cell_type').val(data.cell_type);
            }
        });
    };


    ToolBar.prototype.toggle = function () {
        this.element.toggle();
        IPython.layout_manager.do_resize();
    };


    IPython.ToolBar = ToolBar;

    return IPython;

}(IPython));
