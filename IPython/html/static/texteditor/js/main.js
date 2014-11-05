// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'jquery',
    'base/js/utils',
    'base/js/page',
    'codemirror/lib/codemirror',
    'custom/custom',
], function(
    $, 
    utils,
    page,
    CodeMirror
    ){
    page = new page.Page();

    var base_url = utils.get_body_data('baseUrl');
    var cm_instance = CodeMirror($('#texteditor-container')[0]);
    
    page.show();

});
