var IPython = (function (IPython) {

    var PrintWidget = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    PrintWidget.prototype.style = function () {
        this.element.find('button#print_notebook').button();
        this.element.find('button#print_notebook').attr('title',
            "Open a new window with printer-friendly HTML of the Notebook." +
            " Note that this is incomplete, and may not produce perfect" +
            " printed output." +
            " Make sure to save before printing, to ensure the output is up to date."
            );
    };

    PrintWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find('button#print_notebook').click(function () {
            that.print_notebook();
        });
    };

    PrintWidget.prototype.enable = function () {
        this.element.find('button#print_notebook').button('enable');
    };

    PrintWidget.prototype.disable = function () {
        this.element.find('button#print_notebook').button('disable');
    };

    PrintWidget.prototype.print_notebook = function () {
        var w = window.open('', '_blank', 'scrollbars=1,menubar=1');
        var html = '<html><head>' +
                   $('head').clone().html() +
                   '<style type="text/css">' +
                   '@media print { body { overflow: visible !important; } }' +
                   '.ui-widget-content { border: 0px; }' +
                   '</style>' +
                   '</head><body style="overflow: auto;">' +
                   $('#notebook').clone().html() +
                   '</body></html>';

        w.document.open();
        w.document.write(html);
        w.document.close();

        return false;
    };

    IPython.PrintWidget = PrintWidget;
    
    return IPython;

}(IPython));
