var IPython = (function (IPython) {

    var PrintWidget = function () {
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
