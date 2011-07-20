
//============================================================================
// Cell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    // Base PanelSection class

    var PanelSection = function () {
        if (this.section_name === undefined) {
            this.section_name = 'section';
        };
        this.create_element();
        if (this.element !== undefined) {
            this.bind_events();
        }
        this.expanded = true;
    };


    PanelSection.prototype.bind_events = function () {
        var that = this;
        this.header.click(function () {
            that.toggle();
        });
        this.header.hover(function () {
            that.header.toggleClass('ui-state-hover');
        });
    };


    PanelSection.prototype.create_element = function () {
        this.element = $('<div/>').attr('id',this.id());
        this.header = $('<h3>'+this.section_name+'</h3>').
            addClass('ui-widget ui-state-default section_header');
        this.content = $('<div/>').
            addClass('ui-widget section_content');
        this.element.append(this.header).append(this.content);
        this.create_children();
    };


    PanelSection.prototype.id = function () {
        return this.section_name.toLowerCase() + "_section";
    };


    PanelSection.prototype.expand = function () {
        if (!this.expanded) {
            this.content.slideDown('fast');
//            this.header.addClass('ui-state-active');
//            this.header.removeClass('ui-state-default');
            this.expanded = true;
        };
    };


    PanelSection.prototype.collapse = function () {
        if (this.expanded) {
            this.content.slideUp('fast');
//            this.header.removeClass('ui-state-active');
//            this.header.addClass('ui-state-default');
            this.expanded = false;
        };
    };


    PanelSection.prototype.toggle = function () {
        if (this.expanded === true) {
            this.collapse();
        } else {
            this.expand();
        };
    };


    PanelSection.prototype.create_children = function () {};


    // NotebookSection

    var NotebookSection = function () {
        this.section_name = "Notebook";
        PanelSection.apply(this, arguments);
    };


    NotebookSection.prototype = new PanelSection();


    // CellSection

    var CellSection = function () {
        this.section_name = "Cell";
        PanelSection.apply(this, arguments);
    };


    CellSection.prototype = new PanelSection();


    CellSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
        this.content.find('#collapse_cell').click(function () {
            IPython.notebook.collapse();
        });
        this.content.find('#expand_cell').click(function () {
            IPython.notebook.expand();
        });
        this.content.find('#delete_cell').click(function () {
            IPython.notebook.delete_cell();
        });
        this.content.find('#insert_cell_above').click(function () {
            IPython.notebook.insert_code_cell_before();
        });
        this.content.find('#insert_cell_below').click(function () {
            IPython.notebook.insert_code_cell_after();
        });
        this.content.find('#move_cell_up').click(function () {
            IPython.notebook.move_cell_up();
        });
        this.content.find('#move_cell_down').click(function () {
            IPython.notebook.move_cell_down();
        });
        this.content.find('#to_code').click(function () {
            IPython.notebook.text_to_code();
        });
        this.content.find('#to_text').click(function () {
            IPython.notebook.code_to_text();
        });
    };


    CellSection.prototype.create_children = function () {
        var row0 = $('<div>').
            append($('<span/>').attr('id','toggle').
                append( $('<button>Collapse</button>').attr('id','collapse_cell') ).
                append( $('<button>Expand</button>').attr('id','expand_cell') ) ).
            append($('<span/>').
                append($('<button>X</button>').attr('id','delete_cell')));
        row0.find('#toggle').buttonset();            
        row0.find('button#delete_cell').button();
        this.content.append(row0);

        var row1 = $('<div>').
            append($('<span/>').html('Insert').addClass('button_label')).
            append($('<span/>').attr('id','insert').
                append( $('<button>Above</button>').attr('id','insert_cell_above') ).
                append( $('<button>Below</button>').attr('id','insert_cell_below') ) );
        row1.find('#insert').buttonset();
        this.content.append(row1);

        var row2 = $('<div>').
            append($('<span/>').html('Move').addClass('button_label')).
            append($('<span/>').attr('id','move').
                append( $('<button>Up</button>').attr('id','move_cell_up') ).
                append( $('<button>Down</button>').attr('id','move_cell_down') ) );
        row2.find('#move').buttonset();
        this.content.append(row2);

        var row3 = $('<div>').
            append($('<span/>').html('Cell Type').addClass('button_label')).
            append($('<span/>').attr('id','cell_type').
                append( $('<button>Code</button>').attr('id','to_code') ).
                append( $('<button>Text</button>').attr('id','to_text') ) );
        row3.find('#cell_type').buttonset();
        this.content.append(row3)
    };
//            <span id="move_cell">
//                <button id="move_up">Move up</button>
//                <button id="move_down">Move down</button>
//            </span>
//            <span id="insert_delete">
//                <button id="insert_cell_before">Before</button>
//                <button id="insert_cell_after">After</button>
//                <button id="delete_cell">Delete</button>
//            </span>
//            <span id="cell_type">
//                <button id="to_code">Code</button>
//                <button id="to_text">Text</button>
//            </span>
//            <span id="sort">
//                <button id="sort_cells">Sort</button>
//            </span>
//            <span id="toggle">
//                <button id="collapse">Collapse</button>
//                <button id="expand">Expand</button>
//            </span>
//        </span>


    // KernelSection

    var KernelSection = function () {
        this.section_name = "Kernel";
        PanelSection.apply(this, arguments);
    };


    KernelSection.prototype = new PanelSection();


    IPython.PanelSection = PanelSection;
    IPython.NotebookSection = NotebookSection;
    IPython.CellSection = CellSection;
    IPython.KernelSection = KernelSection;

    return IPython;

}(IPython));

