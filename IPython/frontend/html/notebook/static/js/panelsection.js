
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
        this.content.find('#run_selected_cell').click(function () {
            alert("Not Implemented");
        });
        this.content.find('#run_all_cells').click(function () {
            alert("Not Implemented");
        });
    };


    CellSection.prototype.create_children = function () {

        this.content.addClass('ui-helper-clearfix');

        var row0 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').addClass('cell_section_row_buttons').
                append($('<button>X</button>').attr('id','delete_cell'))).
            append($('<span/>').html('Actions').addClass('cell_section_row_header'));
        row0.find('#delete_cell').button();
        this.content.append(row0);

        var row1 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','insert').addClass('cell_section_row_buttons').
                append( $('<button>Above</button>').attr('id','insert_cell_above') ).
                append( $('<button>Below</button>').attr('id','insert_cell_below') )).
            append($('<span/>').html('Insert').addClass('button_label'));
        row1.find('#insert').buttonset();
        this.content.append(row1);

        var row2 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','move').addClass('cell_section_row_buttons').
                append( $('<button>Up</button>').attr('id','move_cell_up') ).
                append( $('<button>Down</button>').attr('id','move_cell_down') ) ).
            append($('<span/>').html('Move').addClass('button_label'));
        row2.find('#move').buttonset();
        this.content.append(row2);

        var row3 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','cell_type').addClass('cell_section_row_buttons').
                append( $('<button>Code</button>').attr('id','to_code') ).
                append( $('<button>Text</button>').attr('id','to_text') ) ).
            append($('<span/>').html('Cell Type').addClass('button_label'));
        row3.find('#cell_type').buttonset();
        this.content.append(row3);

        var row1 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','toggle_output').addClass('cell_section_row_buttons').
                append( $('<button>Collapse</button>').attr('id','collapse_cell') ).
                append( $('<button>Expand</button>').attr('id','expand_cell') ) ).
            append($('<span/>').html('Output').addClass('button_label'));
        row1.find('#toggle_output').buttonset();
        this.content.append(row1);

        var row0 = $('<div>').addClass('cell_section_row').
            append($('<span/>').attr('id','run_cells').addClass('cell_section_row_buttons').
                append( $('<button>Selected</button>').attr('id','run_selected_cell') ).
                append( $('<button>All</button>').attr('id','run_all_cells') ) ).
            append($('<span/>').html('Run').addClass('button_label'));
        row0.find('#run_cells').buttonset();
        this.content.append(row0);
    };


    // KernelSection

    var KernelSection = function () {
        this.section_name = "Kernel";
        PanelSection.apply(this, arguments);
    };


    KernelSection.prototype = new PanelSection();


    KernelSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
        this.content.find('#restart_kernel').click(function () {
            IPython.notebook.kernel.restart();
        });
        this.content.find('#int_kernel').click(function () {
            IPython.notebook.kernel.interrupt();
        });
    };


    KernelSection.prototype.create_children = function () {

        this.content.addClass('ui-helper-clearfix');

        var row0 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','int_restart').addClass('cell_section_row_buttons').
                append( $('<button>Interrupt</button>').attr('id','int_kernel') ).
                append( $('<button>Restart</button>').attr('id','restart_kernel') )).
            append($('<span/>').html('Actions').addClass('cell_section_row_header'));
        row0.find('#int_restart').buttonset();
        this.content.append(row0);
    };


    // HelpSection

    var HelpSection = function () {
        this.section_name = "Help";
        PanelSection.apply(this, arguments);
    };


    HelpSection.prototype = new PanelSection();


    HelpSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
    };


    HelpSection.prototype.create_children = function () {

        this.content.addClass('ui-helper-clearfix');

        var row0 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','help_buttons0').addClass('cell_section_row_buttons').
                append( $('<button/>').attr('id','python_help').
                    append( $('<a>Python</a>').attr('href','http://docs.python.org').attr('target','_blank') )).
                append( $('<button/>').attr('id','ipython_help').
                    append( $('<a>IPython</a>').attr('href','http://ipython.org/documentation.html').attr('target','_blank') )).
                append( $('<button/>').attr('id','numpy_help').
                    append( $('<a>NumPy</a>').attr('href','http://docs.scipy.org/doc/numpy/reference/').attr('target','_blank') ))).
            append($('<span/>').html('Links').addClass('cell_section_row_header'));
        row0.find('#help_buttons0').buttonset();
        this.content.append(row0);

        var row1 = $('<div>').addClass('cell_section_row ui-helper-clearfix').
            append($('<span/>').attr('id','help_buttons1').addClass('cell_section_row_buttons').
                append( $('<button/>').attr('id','matplotlib_help').
                    append( $('<a>Matplotlib</a>').attr('href','http://matplotlib.sourceforge.net/').attr('target','_blank') )).
                append( $('<button/>').attr('id','scipy_help').
                    append( $('<a>SciPy</a>').attr('href','http://docs.scipy.org/doc/scipy/reference/').attr('target','_blank') )).
                append( $('<button/>').attr('id','sympy_help').
                    append( $('<a>SymPy</a>').attr('href','http://docs.sympy.org/dev/index.html').attr('target','_blank') )));
        row1.find('#help_buttons1').buttonset();
        this.content.append(row1);
    };

    IPython.PanelSection = PanelSection;
    IPython.NotebookSection = NotebookSection;
    IPython.CellSection = CellSection;
    IPython.KernelSection = KernelSection;
    IPython.HelpSection = HelpSection;

    return IPython;

}(IPython));

